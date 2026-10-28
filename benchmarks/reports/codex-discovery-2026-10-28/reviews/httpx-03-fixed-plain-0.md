<!-- run 35076466ab7a4a6fa8c4db3eb9e07df6; model gpt-6.1-sol; only temporary source links normalized -->

Found four defects through static source tracing. The consequences below are derived from code, not runtime observations.

1. **[P1] Environment proxies can bypass an ASGI app.**  
   In [`httpx/_client.py:1441`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1441), `AsyncClient(app=...)` enables environment proxies whenever `trust_env=True` and no explicit transport is supplied.

   **Expected:** Requests using the app shortcut are handled by the supplied ASGI application.  
   **Source-derived consequence:** With a matching `HTTP_PROXY`, `HTTPS_PROXY`, or `ALL_PROXY` configuration and no applicable bypass, requests select a network proxy transport instead. The app never receives them; requests may fail or leave the process unexpectedly.

   **Evidence:** Lines 1455–1467 create proxy mounts, and `_transport_for_url()` at lines 1521–1528 selects matching mounts before the ASGI transport. The synchronous constructor explicitly excludes `app` from environment proxy eligibility at line 693; the asynchronous constructor omits that condition.

2. **[P2] A query in `base_url` causes child paths to become query data.**  
   [`_enforce_trailing_slash()` at line 209](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L209) appends `/` to `url.raw_path`, and `_merge_url()` at lines 390–391 concatenates the child onto that same value.

   **Trigger:** Construct either client with `base_url="https://example.com/api?token=x"`, then build a request for `"users"`.

   **Expected:** The child extends the URL’s path to `/api/users`; path assembly should not modify the query value.  
   **Source-derived consequence:** The resulting URL is `https://example.com/api?token=x/users`. The path remains `/api`, and `token` becomes `x/users`, potentially selecting the wrong endpoint and corrupting authentication parameters.

   **Evidence:** [`URL.raw_path` at line 283](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_urls.py#L283) includes both path and query. `_urlparse.py:183–188` splits a replacement `raw_path` at its first `?`, so the appended child remains inside the query. This affects both clients and the `base_url` setter.

3. **[P2] Authentication retries erase preceding redirects from response history.**  
   In [`httpx/_client.py:966`](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L966), the authentication handler overwrites `response.history` with its older local history after an auth flow yields another request. The asynchronous equivalent is line 1715.

   **Trigger:** With redirects enabled, `/start` returns a redirect to `/protected`; `/protected` returns 401; a custom authentication flow retries `response.request` and receives 200.

   **Expected:** Final history contains the redirect response followed by the 401, and the 401’s history retains the redirect.  
   **Source-derived consequence:** Final history contains only the 401, whose history has also been cleared.

   **Evidence:** Redirect handling accumulates history through local reassignment, `history = history + [response]` at lines 1002 and 1752. Those additions never reach the authentication handler’s list. Its subsequent assignment discards them. This contradicts the documented history contract in `docs/quickstart.md:442–444`.

4. **[P2] Authentication exchanges consume the redirect allowance.**  
   [`_send_handling_redirects()` at line 984](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L984) checks `len(history)` against `max_redirects`, although authentication handling also appends nonredirect responses to that history. The asynchronous equivalents are lines 1718 and 1733.

   **Trigger:** Set `max_redirects=0` and request a protected URL using a fresh `DigestAuth` instance. The server returns a valid Digest challenge.

   **Expected:** Authentication can retry because no redirect occurred.  
   **Source-derived consequence:** The client raises `TooManyRedirects` before sending the authenticated retry. With larger limits, authentication exchanges similarly reduce the available redirect allowance.

   **Evidence:** [`DigestAuth.auth_flow()` at line 199](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_auth.py#L199) receives the challenge and yields an authenticated request at line 222. Client authentication handling first appends the 401 to history, making its length one before the next redirect-limit check.

These are defects rather than open leads; no speculative findings are included. Verification was limited to reading workspace source, documentation, and existing tests. No tests—including runtime integration tests—were executed, no external services were accessed, and no files were modified.