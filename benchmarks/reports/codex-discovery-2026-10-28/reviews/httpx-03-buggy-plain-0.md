<!-- run f19749e814de4382817891a1bbc8a587; model gpt-6.1-sol; only temporary source links normalized -->

Found four defects supported by static source tracing. No files were modified, external services accessed, or runtime integration tests run.

1. **[P1] `AsyncClient(app=...)` can route requests through an environment proxy instead of the app.**

   At [_client.py:1430](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430), environment proxies remain enabled when `app` is supplied and `transport` is omitted. The synchronous constructor explicitly excludes this case.

   **Trigger:** Construct `AsyncClient(app=my_app)` with default `trust_env=True`, a matching `HTTP_PROXY`/`HTTPS_PROXY` setting, and no applicable proxy bypass.

   **Expected:** Requests use the configured ASGI application.

   **Source-traced consequence:** Although `_init_transport()` creates an `ASGITransport`, proxy mounts take precedence in `_transport_for_url()` at [_client.py:1510](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1510). Matching requests use `AsyncHTTPTransport`, bypassing the app and attempting network access through the proxy. The deprecated `app` shortcut is still accepted, so deprecation does not prevent this behavior.

2. **[P2] Direct `send(Request(...))` calls omit the client’s timeout configuration.**

   Both [`Client.send()`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L904) and [`AsyncClient.send()`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1651) dispatch without supplying a timeout when the request lacks one.

   **Trigger:** Create `httpx.Request("GET", url)` directly, then send it using a client configured with `timeout=1.0`, for example.

   **Expected:** The client’s configured timeout applies when the request has no explicit timeout. The supplied timeout documentation promises a default timeout for requests made with that client.

   **Source-traced consequence:** [`Request.__init__()`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_models.py#L335) initializes empty extensions. Timeout insertion happens in `build_request()` at [_client.py:352](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L352), which direct `send()` bypasses. Both default transports forward those extensions to `httpcore` unchanged. Consequently, the configured `1.0` timeout never reaches the transport dependency.

   The omission is established; whether the resulting operation waits indefinitely depends on downstream behavior that was not inspected or executed.

3. **[P2] A query in `base_url` corrupts slash normalization and relative request paths.**

   [`_enforce_trailing_slash()`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L209) and [`_merge_url()`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L390) operate on `raw_path`, which includes both the path and query.

   **Trigger:** Set `base_url="https://example.org/api?token=x"` and build a request for `"items"`.

   **Expected:** Slash normalization affects the path, and the relative request path is appended to `/api/`. It must not become part of the query value.

   **Source-traced consequence:** Construction changes the base URL to `https://example.org/api?token=x/`. Building `"items"` then produces `https://example.org/api?token=x/items`: the path remains `/api`, and `token` changes from `x` to `x/items`.

   Supporting evidence: [`URL.raw_path`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_urls.py#L283) explicitly includes the query, and [`urlparse()`](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_urlparse.py#L183) splits replacement `raw_path` at the first `?`. Both client classes share these methods.

4. **[P2] Authentication retries erase redirects already followed.**

   The redirect handlers extend a local history list using `history = history + [response]`. On an authentication retry, the outer handlers overwrite `response.history` using their older list at [_client.py:955](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L955) and [_client.py:1702](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1702).

   **Trigger:** With redirects enabled, `/start` returns `302` to `/protected`; `/protected` returns `401`; a custom authentication flow retries `response.request` with credentials and receives `200`.

   **Expected:** Final history preserves the followed redirect and authentication response: `[302, 401]`.

   **Source-traced consequence:** The redirect handler initially gives the `401` response history `[302]`. The authentication handler replaces it with `[]`, then appends only the `401` to its own history. The final response therefore contains `[401]`, losing the redirect. The supplied quickstart documents that history includes all followed redirects.

**Open leads and verification limits:** No additional speculative findings are asserted. Exact network timing for finding 2 remains unverified. All consequences above were derived from the supplied source and documentation; no runtime reproduction or integration testing was performed.