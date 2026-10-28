<!-- run 84bf15d358c2437a80fc7a431873d94c; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** [`httpx/_client.py`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py), focusing on transport selection, URL construction, authentication retries, and redirect history. Supporting evidence: URL/parser/auth/transport implementations, documentation, and targeted tests. Nine read-only tool calls; no files modified or runtime tests executed. Concurrent use and exceptional cleanup paths were not fully investigated.  
**Logic Score:** 86/100 — deductions capped per L-code within this module.

Four defects are supported by static traces. Their runtime manifestations and proposed remedies remain untested under the requested discovery protocol.

## Findings

### 🟡 Warning — [L6] Environment proxies override the ASGI app shortcut

**Premises:** The supplied `CHANGELOG.md:608` explicitly promises that `app=...` bypasses environment proxy defaults. `AsyncClient._init_transport()` selects `ASGITransport(app=app)` at `_client.py:1489`.

**Trace:**

1. At [`_client.py:1441`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1441), `trust_env=True` and `transport=None` enable environment proxies even when `app` is supplied.
2. `_get_proxy_map()` imports the proxy configuration; construction installs a corresponding `AsyncHTTPTransport` mount.
3. `_transport_for_url()` at lines 1526–1528 returns that matching mount before the ASGI transport. `_send_single_request()` dispatches to it.

Rebuttal check: explicit `transport=ASGITransport(...)`, `trust_env=False`, or a matching proxy exclusion prevents this path. The deprecated shortcut remains accepted, and its warning recommends the explicit transport as a replacement.

**Divergence:** **L6:** the shortcut fails its transport-selection contract. Requests intended for the local application instead enter the network proxy transport; the application is not invoked.

**Trigger:** Given `HTTP_PROXY=http://proxy.example:8080`, no matching `NO_PROXY` exclusion, and `AsyncClient(app=app, base_url="http://testserver")`, request `/`. Expected: dispatch to `app`. Statically observed dispatch: `AsyncHTTPTransport` through the proxy.

**Remedy:** Replace line 1441 with:

```python
allow_env_proxies = trust_env and app is None and transport is None
```

Dry-run: mentally checked against the synchronous client’s equivalent guard; ordinary network clients still load environment proxies.

**Verification:** Static evidence only; no runtime or remedy execution.

### 🟡 Warning — [L6] Authentication challenges consume the redirect allowance

**Premises:** `_client.py:614–615` defines `max_redirects` as the number of redirect responses followed. Digest authentication normally requires a nonredirecting `401` challenge followed by an authenticated request; `tests/client/test_auth.py:449–460` supports that successful behavior.

**Trace:**

1. `DigestAuth.auth_flow()` receives a `401` with a valid Digest challenge and yields the authenticated request (`_auth.py:199–222`).
2. The client appends the `401` to `history` at `_client.py:969` or 1718.
3. On the next iteration, [`_client.py:984`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L984) or 1733 compares **all** historical responses against `max_redirects`. With zero allowed redirects, `1 > 0` raises `TooManyRedirects` before the authenticated request is sent.

Rebuttal check: the guard runs even when `follow_redirects=False`; no redirect is necessary.

**Divergence:** **L6:** authentication history is mistaken for redirect history. Valid authentication fails with a misleading redirect exception.

**Trigger:** Either client with `max_redirects=0`, `DigestAuth("user", "password")`, and an endpoint returning `401` with `WWW-Authenticate: Digest realm="r", nonce="n", qop="auth"`, then accepting the authenticated request. Expected: complete the second request. Actual traced behavior: `TooManyRedirects` after the first response.

**Remedy:** Replace both guards at lines 984 and 1733 with:

```python
if follow_redirects and sum(
    item.has_redirect_location for item in history
) > self.max_redirects:
```

Dry-run: mentally checked the zero-redirect Digest case and the existing 20/21-redirect boundary; authentication responses no longer count.

**Verification:** Static evidence only; no runtime or remedy execution.

### 🟡 Warning — [L6] Base-URL queries absorb appended request paths

**Premises:** Client URL merging appends relative paths to the base path, supported by `tests/client/test_client.py:204–207`. However, `URL.raw_path` explicitly contains **both path and query** (`_urls.py:283–297`).

**Trace:**

1. Constructing a client with `base_url="https://example.org/api/?token=x"` calls `_enforce_trailing_slash()`.
2. At [`_client.py:210–212`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L210), `raw_path` is `b"/api/?token=x"`. Appending `/` changes the query to `token=x/`.
3. Building a request for `"users"` concatenates the relative bytes onto that value at line 390.
4. `_urlparse.py:183–188` splits at the first `?`, yielding path `/api/` and query `token=x/users`.

Rebuttal check: request construction performs no subsequent path repair. Both clients inherit these methods.

**Divergence:** **L6:** treating `raw_path` as path-only corrupts the query and sends the request to `/api/` instead of `/api/users`.

**Trigger:** The base URL above followed by `build_request("GET", "users")`. Expected path: `/api/users`. Actual constructed URL: `https://example.org/api/?token=x/users`.

**Remedy:** Replace the two method bodies with the following, retaining the base query when the relative URL supplies none:

```python
# _enforce_trailing_slash
path, separator, query = url.raw_path.partition(b"?")
if not path.endswith(b"/"):
    path += b"/"
return url.copy_with(raw_path=path + separator + query)
```

```python
# _merge_url
merge_url = URL(url)
if merge_url.is_relative_url:
    base_path, base_sep, base_query = self.base_url.raw_path.partition(b"?")
    path, separator, query = merge_url.raw_path.partition(b"?")
    suffix = separator + query if separator else base_sep + base_query
    return self.base_url.copy_with(
        raw_path=base_path + path.lstrip(b"/") + suffix
    )
return merge_url
```

Dry-run: mentally checked the trigger, query-free paths, encoded slashes, and absolute URLs. Base-query precedence is an explicit choice in this proposed remedy.

**Verification:** Static evidence only; no runtime or remedy execution.

### 🟡 Warning — [L4] Authentication retries erase preceding redirects

**Premises:** `docs/quickstart.md:442–444` promises that history contains followed redirects in order. Authentication-history tests at `tests/client/test_auth.py:658–707` also require intermediate authentication responses to remain recorded.

**Trace:**

1. With `follow_redirects=True`, `/start` returns `302` to `/private`, which returns `401`. Redirect handling returns the `401` with history `[302]`.
2. A supported custom `Auth` flow yields an authenticated request for `/private`.
3. At [`_client.py:966`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L966), the authentication handler overwrites `response.history` using its older, empty `history` list. It then appends only the `401`.
4. The authenticated `200` consequently receives history `[401]`. The async implementation repeats the overwrite at line 1715.

Rebuttal check: redirect handling extends history by rebinding a local list, so its additions never update the authentication handler’s original list.

**Divergence:** **L4:** overwriting accumulated state drops a followed redirect from the final response and from the intermediate `401`.

**Trigger:** The sequence above, with custom authentication yielding the authenticated `response.request` after the challenge. Expected final history: `[302, 401]`; actual traced history: `[401]`.

**Remedy:** At both lines 966 and 1715, replace:

```python
response.history = list(history)
```

with:

```python
history = list(response.history)
```

Dry-run: mentally checked preservation of `[302, 401]` and the existing authentication-only history sequence.

**Verification:** Static evidence only; no runtime or remedy execution.

## Summary

Prioritize the ASGI routing error and authentication rejection, then URL corruption and lost history. The score describes confirmed findings in this inspected slice, with the prescribed per-code deduction cap; it does not establish whole-file correctness.

## Unresolved Investigations

**U1 — Digest authentication across changed redirect paths:** `_auth.py:265–290` computes the Digest URI from the original request, while redirects can change the path and retain the header. This suggests authentication failure against a server that validates that URI. Server validation and retry-target behavior remain unverified; the next discriminating check is a controlled Digest-server experiment, excluded by this protocol. This lead is not a confirmed finding and does not affect the score.