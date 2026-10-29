<!-- run f449b25808a7460782827f7d977ddacb; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted review of `httpx/_client.py`: URL construction, authentication/redirect handling, and async transport selection, with local supporting files. Not exhaustive.  
**Logic Score:** 72/100

> Four defects are supported by source traces. Consequences below are statically derived, not runtime observations.

## Findings

### 🟡 Warning
**[L5] — Environment proxies bypass the configured ASGI application**

Premises: `AsyncClient(app=...)` promises to send requests to the ASGI application instead of the network (`_client.py:1356–1357`). `trust_env` defaults to `True`.

Trace: [1] At [`_client.py:1430`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430), environment proxies remain enabled when `app` is supplied. [2] `_get_proxy_map()` creates proxy entries; lines 1444–1456 create corresponding network transports. [3] Although `_init_transport()` returns `ASGITransport`, `_transport_for_url()` checks matching proxy mounts first and returns the proxy transport. Rebuttal check: PASSED — `trust_env=False`, an explicit transport, or matching proxy exclusions avoid this path, but none is required. The synchronous constructor already excludes `app` at line 684.

Divergence: L5 — the environment-proxy guard omits the application case. Expected: invoke the ASGI application. Actual traced behavior: select a network proxy transport, bypassing the app; subsequent results depend on that proxy. Tests normally clear proxy variables (`tests/conftest.py:23–44`).

Trigger: With hypothetical `HTTP_PROXY=http://127.0.0.1:9999` and no matching `NO_PROXY`, construct `AsyncClient(app=app)` and request `http://example.org/`. The selected transport is the proxy, not ASGI.

Remedy: Replace line 1430 with:
```python
allow_env_proxies = trust_env and app is None and transport is None
```
Dry-run: ✅ This prevents implicit proxy mounts for `app`; ordinary network clients retain environment proxy support.

Verification: ⚠️ Unverified — runtime integration testing excluded by the requested protocol.

### 🟡 Warning
**[L4] — An authentication retry discards preceding redirect history**

Premises: Redirect handling creates a new local history list. Authentication handling retains its original list. Both redirect responses and intermediate authentication responses belong in response history, as established by `tests/client/test_redirects.py:229–240` and `tests/client/test_auth.py:658–707`.

Trace: [1] Redirect handling appends a redirect using `history = history + [response]` at line 991. [2] It returns the eventual challenge response with that redirect in `response.history`. [3] If authentication yields another request, [`_client.py:955`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L955) replaces this history with the auth handler’s older list, then appends only the challenge response. [4] The next response consequently lacks the earlier redirect. Async lines 1702–1705 repeat this behavior. Rebuttal check: PASSED — inspected tests cover auth and redirect histories separately; no reconciliation exists at this boundary.

Divergence: L4 — stale state overwrites accumulated history. For a `302 → 401 → authenticated 200` sequence, expected final history is `[302, 401]`; actual traced history is `[401]`, and the 401’s own redirect history is erased.

Trigger: A custom `Auth.auth_flow()` yields the initial request, receives a 401 after one followed redirect, then yields `response.request` with an authorization header; the server returns 200.

Remedy: In both authentication handlers, replace `response.history = list(history)` with:
```python
history = list(response.history)
```
Keep the subsequent read and append. Dry-run: ✅ The redirect history becomes the retry’s starting history; auth-only sequences retain their existing order.

Verification: ⚠️ Unverified — runtime integration testing excluded.

### 🟡 Warning
**[L3] — Authentication challenges consume the redirect allowance**

Premises: `max_redirects` limits redirect responses, according to `_client.py:605–606`. Authentication handlers also append nonredirect responses to the same `history` list.

Trace: [1] An initial 401 reaches the authentication flow. [2] When that flow yields an authenticated retry, line 958 appends the 401 to `history`. [3] Before dispatching the retry, [`_client.py:973`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L973) compares the list’s entire length against `max_redirects`. With zero allowed redirects, `1 > 0` raises immediately. Async lines 1705 and 1720 have the same interaction. Rebuttal check: PASSED — the authentication contract explicitly permits multiple requests (`_auth.py:58`); no check excludes authentication responses from this count.

Divergence: L3 — expected: authentication succeeds without following any redirects. Actual traced behavior: `TooManyRedirects` prevents the authenticated request.

Trigger: Set `max_redirects=0`, use `DigestAuth`, and return a valid Digest 401 challenge followed by an authenticated 200. No 3xx response is necessary.

Remedy: In both redirect handlers, count followed redirect responses rather than all historical responses:
```python
if sum(
    r.has_redirect_location and r.next_request is None
    for r in history
) > self.max_redirects:
```
Retain the existing exception body. Dry-run: ✅ A 401 contributes zero; followed redirects contribute one; redirects returned for manual following have `next_request` set and contribute zero.

Verification: ⚠️ Unverified — runtime integration testing excluded.

### 🟡 Warning
**[L6] — Base URL path operations modify query values**

Premises: `URL.raw_path` includes both path and query (`_urls.py:283–297`). Supplying `raw_path` to `copy_with()` splits it at the first `?` (`_urlparse.py:183–188`).

Trace: [1] For `base_url="https://example.org/api?token=x"`, `raw_path` is `/api?token=x`. [2] [`_client.py:209`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L209) appends `/` to that entire value, producing `/api?token=x/`. [3] `_merge_url()` then appends relative path `users`, producing `/api?token=x/users`. Rebuttal check: PASSED — constructors accept this URL without rejecting its query; URL parsing preserves the misplaced suffix inside the query.

Divergence: L6 — the helpers treat a path-and-query property as a path. Expected: append `users` to the path and preserve query value `x`. Actual traced URL: `https://example.org/api?token=x/users`, addressing `/api` with a changed token.

Trigger: `Client(base_url="https://example.org/api?token=x", trust_env=False).build_request("GET", "users").url`.

Remedy: Replace `_enforce_trailing_slash()`’s body with:
```python
path, sep, query = url.raw_path.partition(b"?")
if path.endswith(b"/"):
    return url
return url.copy_with(raw_path=path + b"/" + sep + query)
```
Replace `_merge_url()`’s `merge_raw_path` assignment with:
```python
base_path, base_sep, base_query = self.base_url.raw_path.partition(b"?")
path, sep, query = merge_url.raw_path.partition(b"?")
merge_raw_path = (
    base_path + path.lstrip(b"/")
    + (sep + query if sep else base_sep + base_query)
)
```
Dry-run: ✅ The trigger becomes `/api/users?token=x`; queryless bases retain existing path behavior, and an explicit request query takes precedence.

Verification: ⚠️ Unverified — runtime integration testing excluded.

## Summary

Prioritize the ASGI routing defect, then authentication bookkeeping and URL construction. No files were modified; nine tool calls inspected only workspace material, without external services or history access.

**Open lead, excluded from scoring:** Direct `send(Request(...))` forwards an empty timeout extension without applying the client timeout. This conflicts with the documentation’s default-timeout promise, but the resulting timeout behavior depends on `httpcore`, whose implementation was outside the supplied workspace; an indefinite wait is therefore not established here.