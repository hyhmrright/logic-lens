<!-- run 7d41b72d3e584fbfa155b84ecd57f6fb; model gpt-6.1-sol; only temporary source links normalized -->

Found four defects supported by static control flow. The consequences below are derived from source; they were not observed in runtime tests.

1. **[P1] Environment proxies can bypass the application supplied to `AsyncClient`.**  
   At [httpx/_client.py:1441](httpx/_client.py#L1441), `allow_env_proxies` checks `trust_env` and `transport`, but omits `app`. Consequently, `AsyncClient(app=my_app)` with default options imports environment proxy routes. Those routes take precedence over its ASGI transport in `_transport_for_url()` (lines 1526–1528).

   **Trigger:** A matching HTTP/HTTPS proxy configuration, with no applicable proxy exclusion.

   **Expected:** Requests reach the supplied ASGI application. **Actual consequence:** Requests select `AsyncHTTPTransport` and attempt communication through the proxy instead. The app is bypassed; requests can fail or leave the process unexpectedly.

   Supporting evidence: `_utils.py:195–241` constructs these proxy routes; `_client.py:1455–1467` creates their transports. The synchronous constructor explicitly excludes `app` at line 693.

2. **[P2] A query string in `base_url` absorbs appended request paths.**  
   [httpx/_client.py:209–212](httpx/_client.py#L209) appends a trailing slash to `url.raw_path`. However, [httpx/_urls.py:283–297](httpx/_urls.py#L283) defines `raw_path` as **path plus query**. `_merge_url()` then concatenates the relative request path onto that combined value at `_client.py:390–391`.

   **Trigger:** `base_url="https://example.org/api?token=abc"` and `build_request("GET", "items")`, without additional parameters.

   **Expected:** Append `items` to the path, preserving the query value: `/api/items?token=abc`. **Actual consequence:** Initialization changes the base to `/api?token=abc/`, and merging produces `/api?token=abc/items`. The request targets `/api`, while `token` becomes `abc/items`.

   Supporting evidence: `_urlparse.py:183–186` splits `raw_path` at the first `?`, confirming that the appended text remains inside the query.

3. **[P2] An authentication retry discards redirects already followed.**  
   The redirect handler accumulates history by rebinding its local list at [httpx/_client.py:1002](httpx/_client.py#L1002). The authentication handler retains the earlier list and overwrites `response.history` with it at line 966 before appending the authentication response. The asynchronous implementation repeats this behavior at lines 1715–1718 and 1752.

   **Trigger:** A request follows a `302`, receives a `401`, and a custom authentication flow retries the challenged destination, which returns `200`.

   **Expected:** Final history contains `[302, 401]`; the `401` retains its preceding redirect history. **Actual consequence:** Final history contains only `[401]`, and the challenge response’s redirect history is erased.

   Supporting evidence: `tests/client/test_redirects.py:229–240` expects ordered redirect history, while `tests/client/test_auth.py:658–707` expects intermediate authentication responses and their preceding histories to remain available. Neither inspected case combines the two flows.

4. **[P2] Authentication challenges consume the redirect allowance.**  
   Authentication responses are appended to `history` at [httpx/_client.py:969](httpx/_client.py#L969), while the next redirect-handling invocation checks that entire list against `max_redirects` at line 984. Async equivalents appear at lines 1718 and 1733.

   **Trigger:** A fresh `DigestAuth`, `max_redirects=0`, and an initial `401` containing a valid Digest challenge.

   **Expected:** Send the authenticated retry, since no redirect occurred. **Actual consequence:** `TooManyRedirects` is raised before sending that retry: the authentication response makes the history length one.

   Supporting evidence: `_auth.py:193–222` yields the authenticated retry after a challenge; `_client.py:614–615` describes `max_redirects` as the maximum number of redirect responses to follow.

No additional open lead is presented as a defect. Verification was limited to targeted workspace source and test reads. I did not execute tests, access external services or history, inspect credentials, or modify files. Runtime integration behavior remains unverified.