<!-- run 198089fa56154f65a172ebb875f5eb98; model gpt-6.1-sol; only temporary source links normalized -->

I found four concrete defects by static inspection. The consequences below are derived from source; none were verified at runtime.

1. **`AsyncClient(app=...)` can route requests through an environment proxy instead of the ASGI app.**

   With the default `trust_env=True`, no explicit transport, and a matching environment proxy without a `NO_PROXY` exemption, requests intended for the supplied app select a proxy transport.

   **Expected:** `app=` handles the request locally, as its parameter documentation promises.

   **Actual consequence:** The app is bypassed; the client attempts network traffic through the proxy, potentially exposing request contents or failing to connect.

   **Evidence:** The async constructor’s proxy eligibility check omits `app is None` at [_client.py:1441](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1441). The sync constructor includes that condition at line 693. Although `_init_transport()` creates an ASGI transport, [_transport_for_url():1526](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1526) selects a matching mounted proxy first. The selected HTTP transport delegates to its network pool at [_transports/default.py:375](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_transports/default.py#L375).

2. **A query in `base_url` causes appended paths to become query contents.**

   Example: `base_url="https://example.org/api?token=abc"` followed by `build_request("GET", "items")`.

   **Expected:** The documented path-appending behavior produces path `/api/items`, with query handling separate from the path.

   **Actual consequence:** The constructed URL is `https://example.org/api?token=abc/items`: the endpoint remains `/api`, and the query value changes to `abc/items`. Both clients inherit this behavior.

   **Evidence:** [_enforce_trailing_slash():209](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L209) appends `/` to `raw_path`; [_merge_url():390](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L390) then concatenates the relative request’s `raw_path`. However, [`URL.raw_path`:283](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_urls.py#L283) includes the query. Parsing the result splits at the first `?` in [_urlparse.py:183](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_urlparse.py#L183), leaving the appended path inside the query.

3. **An authentication retry erases redirects already recorded in response history.**

   Consider a supported custom authentication flow: `/start` returns a redirect to `/protected`; `/protected` returns `401`; the auth flow then yields an authenticated request directly to `/protected`, which returns `200`.

   **Expected:** Final history contains the followed redirect and the authentication challenge: `[302, 401]`.

   **Actual consequence:** Final history contains only `[401]`. The challenge response’s own history also loses the redirect, preventing callers from inspecting the complete request chain.

   **Evidence:** Redirect handling accumulates history by rebinding its local list at [_client.py:1002](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L1002). When authentication continues, [_client.py:966](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L966) overwrites that response’s history using the auth handler’s older list, then appends only the challenge response. The async equivalent repeats this at line 1715. The documented history contract includes followed redirects, and existing authentication-history tests cover retries without intervening redirects.

4. **Authentication challenges incorrectly consume the redirect allowance.**

   Configure either client with `max_redirects=0` and fresh `DigestAuth`, then request an endpoint that returns a valid Digest challenge before accepting an authenticated retry.

   **Expected:** Authentication can complete because no redirects occur.

   **Actual consequence:** The client raises `TooManyRedirects` before sending the authenticated retry—even with `follow_redirects=False`.

   **Evidence:** The authentication handlers append challenge responses to `history` at [_client.py:969](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L969) and line 1718. The next iteration passes that same history into redirect handling, which checks its total length against `max_redirects` at [_client.py:984](https://github.com/encode/httpx/blob/6d852d319acd5d97caf14037dff15ede04b37542/httpx/_client.py#L984) and line 1733. Thus one `401` exceeds a zero redirect allowance. [`DigestAuth.auth_flow`:199](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_auth.py#L199) explicitly implements this challenge-and-retry sequence.

Verification was limited to eight read-only shell calls inspecting workspace source, documentation, and tests. No files were modified, external services accessed, or runtime/integration tests executed. No additional open leads are asserted as defects.