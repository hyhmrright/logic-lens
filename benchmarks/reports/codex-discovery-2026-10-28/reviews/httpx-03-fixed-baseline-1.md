<!-- run 3d291852b5274814830eaaeb87dba989; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces through `httpx/_client.py`: request construction, authentication/redirect handling, and asynchronous transport selection, with local supporting files. Convenience methods and transport lifecycle behavior were not exhaustively reviewed.  
**Logic Score:** 79/100

> Four defects are supported by source traces. None was runtime-verified; integration tests were excluded by the requested discovery protocol.

## Findings

### 🟡 Warning
**[L6] — Environment proxies bypass the application supplied to AsyncClient**

Premises: `app=...` selects an in-process `ASGITransport`, as documented in `httpx/_transports/asgi.py:55`. `trust_env` defaults to `True`; an environment proxy may match the request URL.

Trace: [1] [AsyncClient initialization](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1441) allows environment proxies whenever `transport is None`, without checking `app`. [2] `_get_proxy_map()` converts those settings into proxy mounts; `_init_transport()` separately creates the ASGI transport at line 1489. [3] `_transport_for_url()` at line 1526 selects a matching proxy mount before the ASGI transport. `_send_single_request()` dispatches through that selected transport. Rebuttal check: PASSED — the shortcut remains supported despite deprecation; its default arguments admit this path; no fallback invokes the application after proxy selection. The synchronous constructor explicitly excludes `app` at line 693.

Divergence: **L6:** The application shortcut fails to provide the documented in-process transport behavior. Requests matching an environment proxy bypass the application and enter the network transport, potentially returning a proxy response or raising a connection error.

Trigger: Given `HTTP_PROXY=http://127.0.0.1:9999`, no matching `NO_PROXY`, and an ASGI application returning 200, construct `AsyncClient(app=app, base_url="http://testserver")` and request `/`. Expected: application invocation and 200. Source-traced actual: proxy transport selection; the application is never invoked.

Remedy: At line 1441, replace the assignment with:
```python
allow_env_proxies = trust_env and app is None and transport is None
```
Dry-run: ✅ With `app` supplied, implicit proxy mounts disappear and dispatch reaches ASGI; ordinary network clients retain environment proxy behavior.

Verification: ⚠️ Unverified — static trace only; runtime integration tests excluded.

### 🟡 Warning
**[L6] — A query in base_url consumes the appended request path**

Premises: `URL.raw_path` includes both path and query (`httpx/_urls.py:283`). `URL.copy_with(raw_path=...)` splits at the first `?` (`httpx/_urlparse.py:183`). The constructor accepts a base URL containing a query.

Trace: [1] [Trailing-slash enforcement](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L209) receives `/api?key=x` and appends `/`, producing `/api?key=x/`. This changes the query rather than the path. [2] `_merge_url()` at line 390 appends `items` to that complete raw target. [3] URL parsing splits `/api?key=x/items` into path `/api` and query `key=x/items`; `Request` retains that URL. Rebuttal check: PASSED — URL validation accepts this input; relative requests reach the concatenation directly; subsequent request construction does not repair the path.

Divergence: **L6:** The caller treats `raw_path` as a path-only component. Requesting `items` targets `/api`, with `items` embedded in the query value, instead of targeting `/api/items`.

Trigger:
```python
client = httpx.Client(
    base_url="https://example.org/api?key=x",
    transport=httpx.MockTransport(lambda r: httpx.Response(200)),
)
request = client.build_request("GET", "items")
```
Expected path: `/api/items`. Source-traced actual URL: `https://example.org/api?key=x/items`.

Remedy: Keep path and query separate. Replace `_enforce_trailing_slash()` with:
```python
path, sep, query = url.raw_path.partition(b"?")
if not path.endswith(b"/"):
    path += b"/"
return url.copy_with(raw_path=path + sep + query)
```
Replace the relative-URL concatenation at lines 390–391 with the following, preserving the base query unless the relative URL supplies one:
```python
base_path, base_sep, base_query = self.base_url.raw_path.partition(b"?")
path, sep, query = merge_url.raw_path.partition(b"?")
suffix = sep + query if sep else base_sep + base_query
return self.base_url.copy_with(
    raw_path=base_path + path.lstrip(b"/") + suffix
)
```
Dry-run: ✅ The trigger becomes `/api/items?key=x`; encoded path bytes and existing query-free append behavior remain intact.

Verification: ⚠️ Unverified — static trace only; neither original nor proposed replacement was executed.

### 🟡 Warning
**[L3] — Authentication retries consume the redirect allowance**

Premises: `max_redirects` limits redirects (`_client.py:614`). Authentication responses also belong in response history, as established by `tests/client/test_auth.py:658`. Digest authentication retries after a valid 401 challenge (`httpx/_auth.py:199–222`).

Trace: [1] Digest authentication yields the initial request and receives a 401. [2] [Authentication handling](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L966) reads and appends that response to `history`, then attempts the authenticated request. [3] `_send_handling_redirects()` at line 984 compares the entire history length against `max_redirects`. With a limit of zero, `1 > 0` raises before sending the retry. The asynchronous path repeats this at lines 1719 and 1733. Rebuttal check: PASSED — zero is accepted; the standard Digest flow reaches this branch; no exception handler retries or corrects the count.

Divergence: **L3:** A request following zero redirects raises `TooManyRedirects`, preventing successful authentication.

Trigger: Use `max_redirects=0` and fresh `DigestAuth("u", "p")`. A mock handler returns `401` with `WWW-Authenticate: Digest realm="r", nonce="n"` until an Authorization header is present, then returns 200. Expected: two requests and 200. Source-traced actual: one request followed by `TooManyRedirects`.

Remedy: In both redirect loops, replace the length check with:
```python
if sum(item.has_redirect_location for item in history) > self.max_redirects:
```
Dry-run: ✅ The 401 contributes zero redirects, allowing authentication; redirect responses still consume the allowance.

Verification: ⚠️ Unverified — source trace only; runtime integration tests excluded.

### 🟡 Warning
**[L4] — An authentication retry erases preceding redirects from history**

Premises: Redirect handling accumulates history using a new list (`history = history + [response]`). That reassignment does not update the authentication caller’s list. Custom authentication flows may yield another request after receiving a response (`httpx/_auth.py:38–58`).

Trace: [1] Start with authentication history `[]`; `/start` redirects to `/challenge`. [2] Redirect handling returns the challenge response with history `[302]`, while its caller still holds `[]`. [3] If authentication yields another request, [line 966](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L966) overwrites the challenge response’s history with `[]`, then appends only the challenge response. [4] A successful retry therefore receives history `[401]`. The asynchronous equivalent is line 1715. Rebuttal check: PASSED — multi-request authentication is supported; the redirect-plus-retry sequence is reachable; downstream assignments copy the already truncated history.

Divergence: **L4:** Previously followed redirects disappear from both the intermediate response and the final response history.

Trigger: `/start` → `302 Location: /challenge`; `/challenge` → 401; a custom auth flow then yields a request to `/done`, which returns 200. Enable redirect following. Expected final history statuses: `[302, 401]`. Source-traced actual: `[401]`.

Remedy: At lines 966 and 1715, replace:
```python
response.history = list(history)
```
with:
```python
history = list(response.history)
```
Dry-run: ✅ Authentication adopts the accumulated redirect history before appending the challenge; authentication-only sequences retain their existing order.

Verification: ⚠️ Unverified — source trace only; runtime integration tests excluded.

## Summary

Prioritize application transport selection, then URL construction and authentication history accounting. The score deducts once per distinct L-code, as required by the supplied framework.

**Open lead, excluded from scoring:** Both constructors use `proxies or proxy`, collapsing an explicitly empty proxy mapping into the unset case. Environment fallback is evident, but the intended public contract for an empty deprecated mapping needs confirmation.

No files were modified, external services accessed, or runtime integration tests run. Reported actual behavior is derived from source execution traces, not observed runtime output.