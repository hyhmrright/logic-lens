<!-- run a8d1a24429a64d4eba2d0eb07f909511; model gpt-6.1-sol; only temporary source links normalized -->

I found four defects supported by static code tracing. The consequences below are source-derived; I did not execute runtime tests.

1. **[P1] `AsyncClient(app=...)` can bypass the supplied application through an environment proxy.**

   With the default `trust_env=True`, no explicit transport, a matching environment proxy, and no matching `NO_PROXY` exemption, requests select a proxy transport instead of the ASGI application.

   **Expected:** The `app` shortcut dispatches requests to the supplied application, as its constructor documentation specifies.

   **Actual consequence:** Requests attempt network access through the proxy. The application receives no request; callers may receive a proxy response or connection error.

   **Evidence:** [_client.py:1430](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430) permits environment proxies without checking `app`, unlike the synchronous constructor at line 684. Lines 1444–1456 create proxy mounts, and lines 1515–1517 select matching mounts ahead of the default ASGI transport. [_utils.py:195](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_utils.py#L195) shows how environment proxy mappings are constructed. This affects the deprecated but still supported `app` shortcut.

2. **[P2] A query string in `base_url` swallows relative request paths.**

   For either client, consider `base_url="https://example.test/api/?v=1"` followed by `build_request("GET", "users")`.

   **Expected:** The relative path becomes `/api/users`; query handling must not turn the path segment into query data.

   **Actual consequence:** The constructed URL is `https://example.test/api/?v=1/users`. The request targets `/api/`, and `users` becomes part of the query value.

   **Evidence:** [_client.py:209](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L209) appends its trailing slash to `raw_path`, which includes the query. The merge at lines 390–391 then appends the relative path after that query. [_urls.py:283](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_urls.py#L283) confirms that `raw_path` contains both path and query; `_urlparse.py:183–188` splits the resulting string at the first `?`.

3. **[P2] Authentication exchanges incorrectly consume the redirect allowance.**

   A fresh `DigestAuth` request using `max_redirects=0` fails when the server returns a valid Digest challenge, even if there are no redirects and `follow_redirects=False`.

   **Expected:** The authenticated retry proceeds. `max_redirects` is documented as limiting redirect responses.

   **Actual consequence:** The client raises `TooManyRedirects` before sending the authenticated retry. Larger limits similarly restrict multi-request authentication flows.

   **Evidence:** [_client.py:955](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L955) appends authentication responses to `history`; line 973 compares the entire history length against `max_redirects` before every send. Async lines 1702–1705 and 1720 repeat this behavior. [_auth.py:199](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_auth.py#L199) through line 222 establishes that a normal Digest challenge requires a second request. After the first 401, `len(history)` is one, so the zero-limit check raises.

4. **[P2] An authentication retry erases earlier redirect history.**

   Consider a supported custom authentication flow that follows `/start → 302 /protected → 401`, then retries `response.request` and receives 200.

   **Expected:** The final history retains the followed 302 and the intermediate 401. The 401’s own history retains the 302.

   **Actual consequence:** The final history contains only the 401, and that response’s history is emptied. Consumers inspecting the response chain lose evidence of the followed redirect.

   **Evidence:** [_client.py:990](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L990) extends redirect history by rebinding a local list. The enclosing authentication loop retains its original list and overwrites `response.history` with it at line 955 before appending the 401. Async lines 1738–1739 and 1702–1705 have the same interaction. The intended history behavior is supported by `docs/quickstart.md:442` and the authentication-history assertions in `tests/client/test_auth.py:658–707`.

**Open lead — timeout propagation for explicit requests.** Both `send()` methods accept a standalone `Request`, but neither inserts the client timeout when its extensions lack one. `Request` defaults extensions to `{}`, while the default transports forward those extensions unchanged. Consequently, the configured timeout is absent at the transport boundary. I have not classified the downstream timeout consequence as a confirmed defect: HTTPcore’s implementation is outside the supplied workspace, and `send()` also documents sending requests “as-is.”

**Verification limits:** Review was limited to workspace source, documentation, and existing tests, using eight shell invocations. No files were modified, no external services or history were accessed, and no runtime or integration tests were run. Existing tests were read as evidence, not reported as passing.