<!-- run d65bf1e3f6674fc8b93b5bcf1d6eef12; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces of `httpx/_client.py`: request construction, redirect construction, and async transport initialization, including supporting URL/parser/proxy code. This is a partial review.  
**Logic Score:** 86/100

> Two defects are supported by static execution traces. Neither was runtime-verified.

## Findings

### 🟡 Warning
**[L5] — Environment proxies can bypass the configured ASGI app**

Premises: `AsyncClient(app=...)` explicitly promises requests to the ASGI application instead of the network (`_client.py:1367–1368`). `trust_env` defaults to `True`; supplying `app` does not require supplying `transport`.

Trace: [1] At [`_client.py:1441`](httpx/_client.py:1441), `trust_env and transport is None` evaluates to `True` even with an ASGI app configured. [2] `_get_proxy_map()` imports environment proxies; `_utils.py:205–210` converts `HTTP_PROXY` into an `http://` mount. [3] `_init_transport()` creates the ASGI transport at `_client.py:1489–1490`, but the constructor also creates proxy mounts. [4] `_transport_for_url()` returns the matching proxy at `_client.py:1526–1528`, before reaching the ASGI transport. Reachability probe: the synchronous constructor explicitly excludes `app` at line 693; the async constructor lacks that guard. Rebuttal check: PASSED — with the configuration below, no default guard or downstream fallback restores app dispatch.

Divergence: **L5:** Transport selection returns through the proxy branch, bypassing the configured application. Expected: invoke the local ASGI app. Actual behavior implied by the code: select `AsyncHTTPTransport` backed by `httpcore.AsyncHTTPProxy`, then attempt proxy I/O. The app is never invoked; the eventual response or connection error depends on the proxy.

Trigger: Given `HTTP_PROXY=http://127.0.0.1:9999`, no matching `NO_PROXY`, and an ASGI callable `app`, construct `httpx.AsyncClient(app=app)` and request `http://example.test/`.

Remedy: Replace line 1441 with:
```python
allow_env_proxies = trust_env and app is None and transport is None
```
Dry-run: ✅ With `app` supplied, automatic proxy mounts disappear and dispatch reaches ASGI. Ordinary clients retain environment proxy behavior; explicit proxies remain supported.

Verification: ⚠️ Unverified — static trace only; runtime integration tests were excluded by the requested protocol. The existing shortcut test (`tests/test_asgi.py:228–234`) checks construction and deprecation, not dispatch under environment proxies.

### 🟡 Warning
**[L6] — Query-bearing base URLs absorb relative request paths into the query**

Premises: `URL.raw_path` contains **both path and query**, as implemented in [`_urls.py:283`](httpx/_urls.py:283). `copy_with(raw_path=...)` splits that value at the first `?` (`_urlparse.py:183–188`). Relative request construction appends paths to the client’s base path.

Trace: [1] Constructing a client with `base_url="https://example.test/api/?v=1"` passes `b"/api/?v=1"` to `_enforce_trailing_slash()`. [2] At [`_client.py:209`](httpx/_client.py:209), the bytes do not end with `/`, so the function appends `/` **inside the query**, producing `/api/?v=1/`. [3] Building a request for `"users"` reaches `_merge_url()` at `_client.py:390`, which concatenates `b"/api/?v=1/"` and `b"users"`. [4] The URL parser splits `/api/?v=1/users` into path `/api/` and query `v=1/users`; `Request.__init__()` preserves that URL when no additional parameters are supplied. Rebuttal check: PASSED — constructors accept this URL, neither helper separates its components, and request construction supplies no later correction.

Divergence: **L6:** Both helpers treat the callee’s combined path/query representation as a path alone. Expected: address `/api/users` without corrupting `v=1`. Actual statically derived URL: `https://example.test/api/?v=1/users`. This requests a different endpoint and changes the query value.

Trigger:
```python
client = httpx.Client(
    base_url="https://example.test/api/?v=1", trust_env=False
)
request = client.build_request("GET", "users")
# Derived actual: https://example.test/api/?v=1/users
# Expected:       https://example.test/api/users?v=1
```
The shared helpers also affect `AsyncClient`.

Remedy: Replace the two helper implementations with component-aware concatenation:
```python
def _enforce_trailing_slash(self, url: URL) -> URL:
    path, sep, query = url.raw_path.partition(b"?")
    if not path.endswith(b"/"):
        path += b"/"
    return url.copy_with(raw_path=path + sep + query)

def _merge_url(self, url: URLTypes) -> URL:
    merge_url = URL(url)
    if merge_url.is_relative_url:
        base_path, base_sep, base_query = (
            self.base_url.raw_path.partition(b"?")
        )
        path, sep, query = merge_url.raw_path.partition(b"?")
        suffix = sep + query if sep else base_sep + base_query
        return self.base_url.copy_with(
            raw_path=base_path + path.lstrip(b"/") + suffix
        )
    return merge_url
```
Dry-run: ✅ The trigger produces `/api/users?v=1`; a relative query replaces the base query. Query-free bases, encoded paths, and absolute URLs retain their existing behavior.

Verification: ⚠️ Unverified — static trace and mental remedy dry-run only. The inspected base URL tests (`tests/client/test_client.py:184–229`) cover ordinary and encoded paths, without query-bearing bases.

## Summary

Correct the ASGI proxy guard and separate URL paths from queries before concatenating them. This review used nine shell calls, modified no files, accessed no external services, and ran no runtime tests; it does not establish correctness for the untraced remainder.

## Open leads

**Explicit `proxies={}` loses its distinction from omission.** Both constructors pass `proxies or proxy` (`_client.py:694,1442`), converting an empty mapping into `None`; `_get_proxy_map()` then loads environment proxies, although its dictionary branch would otherwise return an empty map. The behavior is clear, but the inspected public contract does not conclusively establish that `{}` must disable environment proxies, so this remains an unscored lead.