<!-- run 269c3c41cb074b1c9eeb323605b29c89; model gpt-6.1-sol; only temporary source links normalized -->

Found three defects supported by static source tracing. The examples below were not executed.

1. **[P2] Generator bodies can acquire conflicting framing headers.**  
   Evidence: [models.py:625](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L625).

   Trigger: prepare a request with `data=(part for part in [b"abc"])` and `headers={"Content-Length": "3"}`.

   **Expected:** use consistent framing—either retain the correct content length or replace it with chunked encoding.

   **Source-derived behavior:** `super_len()` returns zero for this generator, so preparation adds `Transfer-Encoding: chunked` without removing the supplied `Content-Length`. The [adapter’s framing decision](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/adapters.py#L679) then selects `chunked=False` because `Content-Length` exists, and passes both headers downstream. The concrete defect is contradictory headers and framing settings; server rejection or misinterpretation depends on downstream handling and was not verified.

2. **[P2] Seekable body objects without `__iter__` are not rewound for redirects.**  
   Evidence: [models.py:600](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L600).

   Trigger: provide a body wrapper exposing `read()`, `tell()`, and `seek()` around a nonempty `BytesIO`, but no `__iter__`.

   **Expected:** after the first upload consumes the body, a 307/308 redirect should restore its original position before resending it.

   **Source-derived behavior:** this object takes the non-iterable branch. `_encode_params()` accepts it as readable, and `super_len()` can determine its remaining length, but `_body_position` stays `None`: position recording occurs only inside the iterable branch. [Redirect handling](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/sessions.py#L278) consequently skips rewinding. The redirected request retains the consumed body object and its original positive `Content-Length`, leaving no body bytes available to satisfy that length. A server may wait until timeout; that network consequence remains unverified.

3. **[P2] `iter_lines()` inserts empty lines when chunks split CRLF.**  
   Evidence: [models.py:1015](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1015).

   Trigger: body `b"a\r\nb\r\n"` arrives as chunks `b"a\r"` and `b"\nb\r\n"` with the default delimiter.

   **Expected:** yield `[b"a", b"b"]`, regardless of chunk boundaries.

   **Source-derived behavior:** each chunk is processed independently with `splitlines()`. The first chunk yields `b"a"` and clears `pending`; the second chunk’s leading LF therefore yields an extra empty line. The resulting sequence is `[b"a", b"", b"b"]`. This can introduce false record boundaries in line-oriented consumers.

Verification was limited to workspace source, documentation, and test inspection. No tests or runtime integration checks were run, no external services were accessed, and no files were modified. No additional open leads are reported.