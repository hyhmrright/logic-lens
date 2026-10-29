<!-- run 3de54057d3ae4dd3a52edef1aa53d94a; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted review of `httpx/_client.py`: transport selection, authentication retries, and redirect history/limits, with supporting models, transports, utilities, documentation, and tests. Eight read-only tool calls; no history, external services, or file modifications. Convenience methods and lifecycle failure paths were not exhaustively reviewed.  
**Logic Score:** 79/100

Three defects are supported by static traces. Runtime reproduction and remedy execution were excluded by the requested protocol.

## Findings

### 🟡 Warning — [L6] Environment proxies override the supplied ASGI application

**Premises:** `_client.py:1367` documents `app=` as sending requests directly to an ASGI application instead of making network requests. The deprecation message also presents it as equivalent to supplying `ASGITransport(app=...)`.

**Trace:**

1. Construct `AsyncClient(app=app)` with the default `trust_env=True` and no explicit transport.
2. [Line 1441](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1441) enables environment proxies because it checks only `transport is None`.
3. `_utils.py:195–241` converts an applicable `HTTP_PROXY` into an `"http://"` mount. `_client.py:1455–1467` creates its `AsyncHTTPTransport`, although `_init_transport()` separately creates the ASGI transport.
4. `_transport_for_url()` at line 1526 selects the matching proxy mount first. `_send_single_request()` dispatches to it, reaching the proxy connection pool in `_transports/default.py:375`.

Rebuttal check: `NO_PROXY`, `trust_env=False`, or an explicit ASGI transport can prevent this, but none covers the default shortcut path when an environment proxy matches.

**Divergence:** **L6**, line 1441: the documented application shortcut dispatches through a network proxy. The application is never called; the caller receives the proxy/network outcome instead of the application’s response.

**Trigger:** With `HTTP_PROXY=http://proxy.example:8080` and no matching `NO_PROXY`, construct `AsyncClient(app=hello_world, base_url="http://testserver")`, then request `/`. Expected: the application’s response. Actual static consequence: dispatch through `AsyncHTTPTransport` to the configured proxy.

**Remedy:** Replace line 1441 with the same guard used by the synchronous client:

```python
allow_env_proxies = trust_env and app is None and transport is None
```

Dry-run: `app=` now bypasses environment proxy discovery; ordinary network clients retain it.

**Verification:** Static evidence only. No proxy connection or runtime test was attempted; remedy verification is a mental trace.

### 🟡 Warning — [L3] Authentication responses consume the redirect allowance

**Premises:** `_client.py:614–615` and `1361–1362` define `max_redirects` as the maximum number of redirect responses followed. Authentication can legitimately require additional requests: `docs/advanced/authentication.md:29–40` documents the Digest challenge round trip, and `_auth.py:193–222` implements it.

**Trace:**

1. A request made with fresh `DigestAuth` receives a valid `401` Digest challenge without any redirect.
2. `_auth.py:217–222` constructs authorization and yields the retry.
3. `_client.py:969` appends the `401` response to `history`; the async counterpart does this at line 1718.
4. On retry, [line 984](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L984), or async line 1733, evaluates `len(history) > self.max_redirects`. With `max_redirects=0`, `1 > 0` raises `TooManyRedirects` before sending the authenticated request.

Rebuttal check: this guard runs even with `follow_redirects=False`; disabling redirect following does not protect authentication.

**Divergence:** **L3**, lines 984 and 1733: total response history is treated as a redirect count. A successful authentication exchange is aborted despite following zero redirects.

**Trigger:** Use either client with `max_redirects=0`, fresh `DigestAuth("user", "password123")`, and `MockTransport(DigestApp())` from `tests/client/test_auth.py:37`. Request `https://example.org/`. That fixture challenges once, then returns `200`. Expected: `200` with the challenge in history. Actual static consequence: `TooManyRedirects` before the second transport call.

**Remedy:** In both redirect handlers, replace the condition with:

```python
if sum(item.has_redirect_location for item in history) > self.max_redirects:
```

Dry-run: the `401` contributes zero; ordinary redirect responses still consume the allowance. Apply alongside the history-preservation remedy below.

**Verification:** Static evidence only, traced through the real Digest implementation and existing fixture. Neither trigger nor remedy was executed.

### 🟡 Warning — [L4] Authentication retries erase earlier redirects from history

**Premises:** `docs/quickstart.md:442–444` promises that history contains followed redirects in order. `tests/client/test_auth.py:658–707` separately requires intermediate authentication responses to appear in history. Custom authentication may yield multiple requests (`docs/advanced/authentication.md:109–122`).

**Trace:**

1. Start with outer authentication history `[]`. `/start` returns redirect response `R`, followed by `/protected` returning challenge response `A`.
2. The redirect handler rebinds its local history using `history = history + [response]` at line 1002, or async line 1752. It returns `A` with `A.history == [R]`; the outer authentication history remains `[]`.
3. The auth flow yields a retry.
4. [Line 966](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L966), or async line 1715, replaces `A.history` with the outer empty list. Appending `A` then produces `[A]`, permanently losing `R`.

Rebuttal check: when authentication ends immediately, the early return preserves history. The defect specifically requires another yielded authentication request after a followed redirect.

**Divergence:** **L4**, lines 966 and 1715: overwriting the returned history discards redirects already followed. Callers inspecting the final response receive an incomplete request chain.

**Trigger:** With `follow_redirects=True`, return `302 Location: /protected` for `/start`; return `401` for `/protected` without `X-Authentication`; otherwise return `200`. A custom auth flow retries `response.request` once with that header. Expected final history: `[302, 401]`. Actual static consequence: `[401]`, with the challenge’s own redirect history also erased.

**Remedy:** Replace each `response.history = list(history)` inside `_send_handling_auth()`—lines 966 and 1715—with:

```python
history = list(response.history)
```

Keep the subsequent response read and `history.append(response)`.

Dry-run: redirects returned by the inner handler are retained before appending the challenge. Without redirects, the existing authentication-history ordering is preserved.

**Verification:** Static evidence only. The operation sequence and proposed replacement were mentally traced; no runtime or regression tests ran.

## Summary

Prioritize the ASGI routing defect, which can unexpectedly send application requests through a network transport. The two authentication/redirect defects affect both client variants and should be addressed together.

The score reflects confirmed findings in this inspected slice, not whole-file correctness or shipping readiness. No additional open lead was developed sufficiently to report; lifecycle exception handling and remaining URL-merging boundaries remain unassessed.