<!-- run db2c62641b4d452aaea3e590a365dab3; model gpt-6.1-sol; only temporary source links normalized -->

Found four concrete defects by static inspection. The consequences below follow from the source; none were verified at runtime.

1. **[P1] URL passwords are included in INFO logs — both clients.**  
   Evidence: [sync logging](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1028) and async lines 1775–1781 interpolate `request.url` with `%s`. In `_urls.py`, `URL.__str__()` returns the complete URL, including userinfo; only `__repr__()` masks passwords. `_auth.py:135–137` adds Basic authentication without removing credentials from the URL.

   **Trigger/consequence:** after a response to `https://alice:secret@example.com/`, enabled INFO logging records that URL with `secret` intact. Credentials should be redacted from routine request logs. This disclosure requires credentials embedded in the URL; using only `auth=(...)` does not create this particular exposure.

2. **[P1] Environment proxies can bypass an explicitly supplied ASGI application.**  
   Evidence: [async proxy configuration](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430) permits environment proxies whenever `trust_env` is true and `transport` is absent, even when `app` is supplied. Although `_init_transport()` creates an `ASGITransport`, proxy mounts take precedence in `_transport_for_url()` at lines 1515–1517. The synchronous constructor explicitly excludes `app` at line 684.

   **Trigger/consequence:** with a matching `HTTP_PROXY` and no applicable `NO_PROXY` exclusion, `AsyncClient(app=app, base_url="http://testserver")` routes requests through the network proxy instead of invoking `app`. Expected behavior is dispatch to the supplied application. Requests can therefore fail unexpectedly or leave the process through the proxy. The shortcut is deprecated but remains supported; `tests/test_asgi.py:227–234` checks only its warning and construction.

3. **[P2] An explicit empty proxy mapping unexpectedly enables environment proxies — both clients.**  
   Evidence: [sync constructor](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L684) passes `proxies or proxy` to `_get_proxy_map()`; async lines 1430–1431 do the same. For `proxies={}` and the default `proxy=None`, this becomes `None`. `_get_proxy_map()` distinguishes these values: `None` loads environment proxies, whereas an empty dictionary produces no proxy entries.

   **Trigger/consequence:** with a matching environment proxy, `Client(proxies={})` or `AsyncClient(proxies={})` uses that proxy despite the explicit empty configuration. Expected behavior is an empty proxy map. The existing empty-map case in `tests/client/test_proxies.py:88` does not exercise this condition: the autouse fixture in `tests/conftest.py:34–45` removes proxy environment variables.

4. **[P2] A query in `base_url` corrupts relative URL construction — both clients.**  
   Evidence: [trailing-slash enforcement](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L209) appends `/` to `url.raw_path`, and `_merge_url()` at lines 390–391 concatenates the relative path onto it. `_urls.py:283–297` establishes that `raw_path` contains **both path and query**; `_urlparse.py:183–188` splits it at the first `?`.

   **Trigger/consequence:** with `base_url="https://example.com/api?token=abc"`, building a request for `"users"` produces `https://example.com/api?token=abc/users`. Expected behavior is to append `users` to the path, yielding `/api/users`; instead, the endpoint remains `/api` and the token value becomes `abc/users`. This path corruption exists regardless of the intended query-inheritance policy.

**Open lead, not a confirmed defect:** direct `send(httpx.Request(...))` does not add the client timeout. `Request` starts with empty extensions, timeout insertion occurs in `build_request()`, and the default transports forward extensions unchanged. This appears inconsistent with the documented default timeout, but `send()` also promises an unmodified request, and downstream behavior for a missing timeout extension is not established by the inspected workspace code. I therefore cannot substantiate a claim that these calls wait indefinitely.

Verification was limited to nine read-only shell/tool calls within the supplied workspace. No files were modified, no external services or history were accessed, and no tests—including runtime integration tests—were run.