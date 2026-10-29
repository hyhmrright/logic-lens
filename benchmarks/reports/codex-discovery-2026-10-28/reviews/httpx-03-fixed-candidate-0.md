<!-- run 5493c3cb332348d08db7e60735a10f04; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted review of `httpx/_client.py`: authentication, redirects, transport selection, and response handling, supported by local implementations, tests, and documentation. Eight tool calls used. URL merging and exceptional transport cleanup were not fully investigated.  
**Logic Score:** 86/100

Three defects are supported by static execution traces. No runtime integration tests were run; all consequences below are statically established, not runtime observations. No files were modified or external services accessed.

## Findings

### 🟡 Warning — [L6] Environment proxies can bypass the supplied ASGI app

**Premises:** The `AsyncClient` contract at `_client.py:1367` says `app=` sends requests to the ASGI application instead of making network requests. The deprecated shortcut remains accepted; its warning recommends the equivalent explicit ASGI transport.

**Trace:**

1. At [`_client.py:1441`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1441), default `trust_env=True` and omitted `transport` enable environment proxies even when `app` is supplied.
2. `_get_proxy_map()` and `_utils.get_environment_proxies()` convert `HTTP_PROXY` into an `http://` mount. `_init_transport()` separately creates the intended `ASGITransport`.
3. `_transport_for_url()` at line 1526 selects matching mounts before the default transport, returning `AsyncHTTPTransport` for an HTTP URL.
4. That transport forwards the request to its proxy pool at `_transports/default.py:375`, bypassing the ASGI app.

Rebuttal check: `trust_env=False`, an explicit transport, or a matching `NO_PROXY` exclusion prevents this path. None is required by the `app=` contract. The synchronous constructor already excludes `app` from environment proxy eligibility.

**Divergence:** **L6:** Transport selection violates the application shortcut’s dispatch contract. The application receives no request; the client selects the network proxy path, which can return an unrelated response or fail.

**Trigger:** Configure `HTTP_PROXY=http://127.0.0.1:9999`, with no applicable proxy exclusion. Construct `AsyncClient(app=hello_world)` and request `http://testserver/`. Expected: the app’s response. Actual selection: the proxy transport.

**Remedy:** Replace line 1441 with:

```python
allow_env_proxies = trust_env and app is None and transport is None
```

Dry-run: supplied apps retain their ASGI transport; ordinary clients still use environment proxies. Explicit proxy configuration remains supported.

**Verification:** Static evidence only. The dispatch chain was inspected; no proxy connection or ASGI integration test was executed. Remedy checked mentally.

### 🟡 Warning — [L6] Authentication responses incorrectly exhaust the redirect limit

**Premises:** `_client.py:614` defines `max_redirects` as the maximum number of **redirect responses followed**. Authentication may issue multiple requests (`_auth.py:58`), and Digest authentication retries a 401 challenge (`_auth.py:199–222`). Such challenges are not redirects.

**Trace:**

1. An initial Digest request returns a valid 401 challenge without any redirection.
2. `_send_handling_auth()` obtains the authenticated retry and appends the 401 response to `history` at line 969.
3. The next call enters [`_send_handling_redirects()` at line 984](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L984).
4. With `max_redirects=0`, `len(history) > self.max_redirects` evaluates as `1 > 0`, raising `TooManyRedirects` before sending the authenticated request.

Rebuttal check: the guard does not distinguish authentication responses from redirects and runs even with `follow_redirects=False`. Async lines 1718 and 1733 have the same behavior.

**Divergence:** **L6:** The redirect handler assumes the caller’s history contains only redirects, although the authentication caller also records challenges. Valid authentication fails despite following zero redirects.

**Trigger:** Use either client with `max_redirects=0`, fresh `DigestAuth`, and an endpoint that returns a valid Digest challenge followed by 200 for the authenticated retry. Expected: 200 after authentication. Actual: `TooManyRedirects`; the retry is never sent.

**Remedy:** Replace the guard at lines 984 and 1733 with:

```python
if follow_redirects and sum(
    item.has_redirect_location for item in history
) > self.max_redirects:
```

Apply the history-preservation remedy below as well so redirects survive authentication transitions. Dry-run: a 401 contributes zero; a followed redirect contributes one; the existing redirect boundary remains enforced.

**Verification:** Static evidence only; no authentication integration test executed. Remedy checked mentally against zero redirects, disabled following, and the redirect-limit boundary.

### 🟡 Warning — [L4] Authentication retries erase preceding redirect history

**Premises:** `docs/quickstart.md:442–444` requires response history to retain followed redirects in order. `tests/client/test_auth.py:684–707` establishes that authentication intermediates also belong in history. These requirements both apply when a request redirects before authentication completes.

**Trace:**

1. An initial request redirects from `/start` to `/protected`, which returns 401.
2. The redirect handler creates a new local list at line 1002. It returns the 401 with `response.history=[redirect_response]`; the authentication handler’s original `history` remains empty.
3. A custom authentication flow yields another request for `/protected`.
4. [`_client.py:966`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L966) overwrites the 401’s history with that empty list. Line 969 retains only the 401.
5. The authenticated 200 response consequently receives history `[401]`.

Rebuttal check: if authentication finishes without retrying, the overwrite is skipped. The defect requires another yield after the redirect chain. Async lines 1715–1718 repeat the same mutation.

**Divergence:** **L4:** Replacing populated response state with the caller’s stale history discards a followed redirect. Expected status history: `[302, 401]`; actual: `[401]`. The intermediate 401 also loses its own redirect history.

**Trigger:** With `follow_redirects=True`, serve `/start → 302 /protected → 401`; let custom auth retry `response.request` with the required token, producing 200.

**Remedy:** At lines 966 and 1715, replace:

```python
response.history = list(history)
```

with:

```python
history = list(response.history)
```

Keep the subsequent append. Dry-run: the redirect is preserved before appending the challenge; authentication-only and redirect-only histories retain their existing ordering.

**Verification:** Static evidence only; no combined authentication/redirect test executed. Remedy checked mentally.

## Summary

Prioritize the ASGI routing defect wherever `app=` is still used, then correct the authentication/history interaction. These are confirmed static findings, not open leads; the untraced areas listed in Scope remain unassessed.

The score describes this inspected slice only. It applies the supplied per-module deduction cap: one Warning deduction each for L6 and L4.