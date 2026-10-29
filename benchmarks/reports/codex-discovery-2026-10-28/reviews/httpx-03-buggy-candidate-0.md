<!-- run 2a092a4f564f44c994b5a8d2dc0e61f2; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Focused static review of `httpx/_client.py`: request timeouts, authentication/redirect history, and ASGI transport selection, supported by local models, transports, utilities, documentation, and tests. Lifecycle and concurrency paths were not exhaustively reviewed. Nine read-only shell calls; no files modified or runtime tests executed.  
**Logic Score:** 86/100

Three defects are supported by static traces. The score counts confirmed findings in this slice, with one deduction per L-code per module; it does not measure whole-project correctness.

## Findings

### 🟡 Warning — [L6] Environment proxies bypass the configured ASGI application

**Premises:** `AsyncClient` documents `app` as an ASGI application receiving requests instead of actual network requests (`httpx/_client.py:1356`). The deprecated shortcut remains supported, as demonstrated by `tests/test_asgi.py:228`.

**Trace:**

1. At [`_client.py:1430`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430), constructing `AsyncClient(app=app)` with default `trust_env=True` enables environment proxies because `transport is None`; `app` is not checked.
2. `_get_proxy_map()` obtains proxy mounts from `get_environment_proxies()`. An `HTTP_PROXY` value creates an `http://` mount (`httpx/_utils.py:202–210`).
3. `_init_transport()` creates the intended `ASGITransport`, but the constructor also creates the proxy transport.
4. `_transport_for_url()` returns the matching proxy transport before reaching the default ASGI transport (`_client.py:1515–1519`). `_send_single_request()` invokes that proxy transport.

Rebuttal check: supplying an explicit ASGI transport disables environment proxies, and the sync constructor checks `app is None`. Neither defense covers the async `app=` shortcut.

**Divergence:** **L6 — Callee Contract Mismatch:** the selected transport does not fulfill the configured application-dispatch contract. The local application is bypassed and a network request is attempted through the environment proxy.

**Trigger:** With `HTTP_PROXY=http://proxy.example:8080`, no matching `NO_PROXY` exemption, and no explicit proxy/mount override, construct `AsyncClient(app=app)` and request `http://service.example/`. Expected: invoke `app`. Actual traced behavior: select `AsyncHTTPTransport` for the proxy.

**Remedy:** Replace line 1430 with:

```python
allow_env_proxies = trust_env and app is None and transport is None
```

Dry-run: disables implicit proxies for `app=`, matching the sync constructor; ordinary network clients retain existing behavior. Explicit proxy configuration remains effective.

**Verification:** Static evidence only. No runtime routing or network test was performed.

### 🟡 Warning — [L6] Directly constructed requests omit the client timeout

**Premises:** `docs/advanced/clients.md:148–158` explicitly supports constructing `httpx.Request(...)` and submitting it through `client.send()`. `docs/advanced/timeouts.md:30–37` promises the client timeout as the default for requests made with that client. `docs/advanced/extensions.md:139` identifies the request’s `"timeout"` extension as the mechanism carrying these settings through the stack.

**Trace:**

1. `Request("GET", url)` initializes `extensions` to `{}` (`httpx/_models.py:335`).
2. [`Client.send()` at line 904](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L904) checks client state, resolves redirects/authentication, and dispatches without adding timeout settings. `AsyncClient.send()` follows the same sequence.
3. `_send_single_request()` passes the request to the selected transport.
4. The default transports forward `request.extensions` unchanged to `httpcore.Request` (`httpx/_transports/default.py:222–235` and `362–375`). The configured client timeout never reaches that boundary.

Rebuttal check: `build_request()` supplies the timeout extension at `_client.py:351–358`, protecting requests made through `get()` and related helpers. Direct construction bypasses it.

**Divergence:** **L6 — Callee Contract Mismatch:** the send path relies on a request already containing timeout configuration, although the supported `Request` constructor supplies none. The client’s configured deadline is omitted, defeating the documented timeout guarantee on this path.

**Trigger:** Construct `Client(timeout=0.1, trust_env=False)` and call `send(httpx.Request("GET", "http://service.example/"))`; equivalently use `AsyncClient`. Expected transport extensions contain `connect`, `read`, `write`, and `pool` values of `0.1`. Actual traced extensions are `{}`. Requests built with `client.build_request()` carry those values.

**Remedy:** In both `send()` implementations, before dispatch, insert:

```python
if "timeout" not in request.extensions:
    request.extensions["timeout"] = self.timeout.as_dict()
```

Dry-run: supplies defaults for direct requests while preserving explicit request timeout extensions, including disabled timeouts.

**Verification:** Static evidence only. Omission at the transport boundary is established. Actual waiting duration and the external `httpcore` fallback behavior were not experimentally verified or inspected outside the workspace.

### 🟡 Warning — [L4] Authentication retries erase preceding redirect history

**Premises:** `docs/quickstart.md:442–444` promises that response history contains followed redirects in order. `tests/client/test_auth.py:658–707` separately establishes that authentication intermediates also belong in response history. Custom authentication flows may yield multiple requests (`httpx/_auth.py:38–58`).

**Trace:**

1. An authentication attempt receives redirect response `R`, then challenge response `C`. `_send_handling_redirects()` assigns `C.history = [R]` using its locally extended history (`_client.py:985–991`).
2. The authentication flow yields another request.
3. At [`_client.py:955`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L955), `response.history = list(history)` replaces `C.history` with the outer authentication history, still `[]`.
4. Only `C` is appended to that outer history. If the next request returns success without redirecting, its history becomes `[C]`; `R` has disappeared. The async implementation repeats this at line 1702.

Rebuttal check: ordinary redirect handling preserves history, and authentication tests cover retries without redirects. Neither covers the combined sequence.

**Divergence:** **L4 — State Mutation Hazard:** overwriting the callee’s accumulated history discards an actual followed redirect. Both the challenge response’s history and the final response’s history become incomplete.

**Trigger:** A supported custom authentication flow yields `/start`, which returns `302 → /protected`; `/protected` returns `401`. The flow then yields a second request returning `200` directly. With `follow_redirects=True`, expected final history is `[302, 401]`; actual traced history is `[401]`.

**Remedy:** At both lines 955 and 1702, replace:

```python
response.history = list(history)
```

with:

```python
history = list(response.history)
```

Keep the subsequent `history.append(response)`.

Dry-run: retains redirects before adding the authentication response. Authentication without redirects and redirect-only flows retain their existing ordering.

**Verification:** Static evidence only. Neither the combined sequence nor the remedy was executed.

## Summary

Prioritize ASGI routing and timeout propagation, then history preservation. All remedies above were checked by source tracing only; runtime integration tests were excluded by the requested protocol.

## Unresolved Investigations

**Base URLs containing queries:** `URL.raw_path` includes the query (`httpx/_urls.py:283–297`), while `_enforce_trailing_slash()` and `_merge_url()` append separators and relative paths to that combined value. This suggests query corruption, but the inspected contracts do not establish the intended semantics for query-bearing base URLs. The next check is an explicit contract or existing requirement covering that case. This remains an open lead and does not affect the score.