<!-- run 188977c81dcd4ad99b548bc49f4b8e62; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `httpx/_client.py`, prioritizing request URL construction and proxy/transport selection, with targeted supporting reads. Lifecycle and concurrency paths were not exhaustively reviewed.  
**Logic Score:** 86/100

> Three defects supported by static execution traces. Consequences below are derived from source, not runtime observations.

## Findings

### 🟡 Warning
**[L6] — Environment proxies bypass an explicitly supplied ASGI app**

Premises: `AsyncClient(app=...)` selects `ASGITransport` when no explicit transport is supplied. Its documented purpose is to dispatch to the application instead of making network requests. Environment proxy mounts take precedence over the default transport.

Trace: [1] At [_client.py:1430](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430), `trust_env=True` and `transport=None` enable environment proxies even when `app` is supplied. [2] Lines 1444–1456 create proxy transport mounts, while line 1479 separately creates the ASGI default transport. [3] `_transport_for_url()` at line 1515 returns a matching proxy mount before reaching the ASGI fallback. Rebuttal check: PASSED — no app-specific exclusion exists; the synchronous constructor explicitly includes `app is None` at line 684. An applicable `NO_PROXY` entry prevents this particular trigger.

Divergence: **L6:** A matching environment proxy causes the request to use `AsyncHTTPTransport`; the supplied application receives no call. Instead, the client attempts network proxy dispatch, potentially returning an unrelated response or a connection error.

Trigger: Given effective proxy configuration `HTTP_PROXY=http://proxy.example:8080`, no applicable `NO_PROXY`, and no explicit mounts:
```python
client = httpx.AsyncClient(app=my_app, base_url="http://testserver")
await client.get("/")
```
Expected: dispatch to `my_app`. Source-traced result: select the environment proxy transport.

Remedy: Replace line 1430 with:
```python
allow_env_proxies = trust_env and app is None and transport is None
```
Dry-run: ✅ App dispatch remains local; ordinary network clients retain environment proxy support; explicit proxy configuration remains available.

Verification: ⚠️ Unverified by execution — no runtime integration tests were run.

### 🟡 Warning
**[L3] — An empty proxy mapping is treated as an omitted mapping**

Premises: `_get_proxy_map()` distinguishes `None` from a dictionary: `None` permits environment discovery, while a dictionary is converted directly. An empty dictionary therefore produces no proxy mounts when passed through intact.

Trace: [1] At [_client.py:685](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L685), `proxies={}` and the default `proxy=None` evaluate through `proxies or proxy` to `None`. The asynchronous constructor repeats this at line 1431. [2] `_get_proxy_map()` enters its `None` branch at line 217 and loads environment proxies. [3] Matching mounts then override the direct transport. Rebuttal check: PASSED — no later guard restores the explicit empty mapping. The existing empty-mapping test expects direct transport, but [tests/conftest.py:34](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/tests/conftest.py#L34) clears proxy variables, masking this distinction.

Divergence: **L3:** Explicitly configuring zero proxies can still route requests through an environment proxy. Expected behavior follows the helper’s dictionary branch: no proxy mounts.

Trigger: With effective `HTTP_PROXY=http://proxy.example:8080` and no matching bypass:
```python
client = httpx.Client(proxies={})
transport = client._transport_for_url(httpx.URL("http://example.com"))
```
Expected: `transport is client._transport`. Source-traced result: a proxy transport. `AsyncClient` has the same defect.

Remedy: In both constructors, replace:
```python
self._get_proxy_map(proxies or proxy, allow_env_proxies)
```
with:
```python
self._get_proxy_map(
    proxies if proxies is not None else proxy, allow_env_proxies
)
```
Dry-run: ✅ `{}` reaches the dictionary branch and yields no mounts; omitted configuration still permits environment discovery; nonempty mappings retain their behavior.

Verification: ⚠️ Unverified by execution — no runtime integration tests were run.

### 🟡 Warning
**[L6] — Base URL queries absorb appended request paths**

Premises: `URL.raw_path` includes both path and query, as implemented in [_urls.py:283](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_urls.py#L283). Copying a `raw_path` splits at the first `?` in `_urlparse.py:183`. Base URLs containing queries are accepted without validation.

Trace: [1] Given `https://example.com/api?x=1`, `_enforce_trailing_slash()` at [_client.py:209](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L209) appends `/` to `b"/api?x=1"`, producing query `x=1/` while leaving path `/api`. [2] `_merge_url()` at line 390 concatenates that complete path/query with `b"items"`. [3] Parsing `b"/api?x=1/items"` again yields path `/api` and query `x=1/items`. Rebuttal check: PASSED — the constructor and base URL setter accept this input, and request construction does not repair the result.

Divergence: **L6:** Path operations use a property whose contract includes the query. The request targets the wrong endpoint and changes the query value. This affects both client classes through `BaseClient`.

Trigger:
```python
client = httpx.Client(base_url="https://example.com/api?x=1")
request = client.build_request("GET", "items")
```
Expected path: `/api/items`, with query handled separately. Source-traced URL: `https://example.com/api?x=1/items`.

Remedy: Separate the path and query before appending. Replace `_enforce_trailing_slash()`’s body with:
```python
path, sep, query = url.raw_path.partition(b"?")
if not path.endswith(b"/"):
    path += b"/"
return url.copy_with(raw_path=path + sep + query)
```
Replace lines 390–391 with the following policy: inherit the base query unless the relative URL supplies one.
```python
base_path, sep, query = self.base_url.raw_path.partition(b"?")
relative_path = merge_url.raw_path.lstrip(b"/")
if b"?" in relative_path:
    sep = query = b""
return self.base_url.copy_with(
    raw_path=base_path + relative_path + sep + query
)
```
Dry-run: ✅ The trigger becomes `/api/items?x=1`; explicit relative queries replace the base query; query-free and percent-encoded paths retain existing append behavior.

Verification: ⚠️ Unverified by execution — remedies were traced mentally, not executed.

## Summary

Prioritize the proxy routing defects because configuration can unexpectedly change the destination of a request. The score deducts seven points for each distinct confirmed category, L3 and L6, following the supplied per-category cap.

Eight read-only tool calls were used. No files were modified, external services accessed, or runtime tests executed.

### Open lead — excluded from findings and score

Direct `send(httpx.Request(...))` carries no timeout extension: `Request` initializes empty extensions, and neither `send()` implementation inserts the client timeout. The default transport forwards those extensions unchanged. This conflicts with the timeout guide’s “everywhere” wording, but `send()` explicitly promises unmodified requests. The missing metadata is established; whether it constitutes a defect, and its downstream timeout consequence, remain unresolved within this review.