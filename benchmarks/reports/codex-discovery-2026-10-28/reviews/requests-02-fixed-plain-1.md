<!-- run 9009e32b49f24e0d9e0dabc86b506b9b; model gpt-6.1-sol; only temporary source links normalized -->

Found three concrete defects by static source tracing. The outcomes below were not runtime-tested.

1. **`iter_lines()` inserts blank lines when CRLF crosses a chunk boundary.**  
   Evidence: [models.py:1018](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1018).

   For content `b"a\r\nb\r\n"` and `chunk_size=2`, the chunks are `b"a\r"`, `b"\nb"`, and `b"\r\n"`. The implementation treats the first chunk’s trailing `\r` as a complete line ending and retains no pending state. The next chunk’s leading `\n` therefore produces an empty line.

   **Expected:** `[b"a", b"b"]`, independent of chunk boundaries.  
   **Source-derived result:** `[b"a", b"", b"b"]`. With `chunk_size=3`, the same content produces the expected two lines. This can introduce spurious records when processing streamed text. Cached responses are also affected because [utils.py:621](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/utils.py#L621) slices their content at the requested chunk size.

2. **Preparing an iterator body can produce conflicting framing headers.**  
   Evidence: [models.py:625](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L625).

   Consider preparing a POST with `data=iter([b"abc"])` and `headers={"Content-Length": "3"}`. The iterator has no discoverable length, so `super_len()` returns zero. The body preparation code adds `Transfer-Encoding: chunked` without removing or respecting the supplied `Content-Length`.

   **Expected:** one consistent framing scheme—retain the correct length and omit chunked encoding, or remove the length and use chunked encoding.  
   **Source-derived result:** both `Content-Length: 3` and `Transfer-Encoding: chunked` remain. Additionally, [adapters.py:679](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/adapters.py#L679) selects `chunked=False` because `Content-Length` exists, contradicting the prepared transfer-encoding header.

   The contradictory prepared state and adapter argument are established. The resulting wire bytes and server response remain unverified.

3. **Pickling a response breaks its public `.next` property.**  
   Evidence: [models.py:750](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L750), [models.py:824](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L824), and [models.py:890](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L890).

   `_next` is initialized by `__init__`, but omitted from serialized `__attrs__`. Unpickling bypasses `__init__`, and `__setstate__` never restores `_next`. The `.next` getter accesses that missing attribute directly.

   **Expected:** after a pickle round trip, `.next` returns `None` for an ordinary response or preserves the prepared redirect request.  
   **Source-derived result:** accessing `.next` raises `AttributeError`; pending redirect information is also lost. [sessions.py:818](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/sessions.py#L818) populates this information when redirects are disabled. The existing pickle test checks only the restored request’s URL and headers.

Verification was limited to eight read-only tool calls within the supplied workspace. No files were modified, no external services were accessed, and no runtime or integration tests were run. The wire-level consequence in finding 2 remains an open verification lead; it is not a demonstrated server failure.