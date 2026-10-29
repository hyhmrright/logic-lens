<!-- run 3ae81e87ea9a43cf85347386396b6d23; model gpt-6.1-sol; only temporary source links normalized -->

Found three defects supported by static tracing. Examples below were **not executed**.

1. **[P2] Generator uploads can acquire conflicting framing headers** — [models.py:625](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L625)

   Trigger: prepare a POST with `data=iter([b"abc"])` and `headers={"Content-Length": "3"}`.

   **Expected:** Preserve the valid explicit length without adding chunked transfer encoding, or reject the combination.

   **Code-derived result:** The prepared request contains both `Content-Length: 3` and `Transfer-Encoding: chunked`. `super_len()` returns zero for this iterator (`utils.py:160–228`), so `prepare_body()` adds the transfer-encoding header without checking the existing content length.

   This also conflicts with the transport decision: `HTTPAdapter.send()` selects `chunked=False` whenever `Content-Length` exists (`adapters.py:679`) and forwards both headers to urllib3. The conflicting prepared headers and adapter decision are established; exact wire output and server handling remain unverified.

2. **[P2] `iter_lines()` invents empty lines when CRLF crosses a chunk boundary** — [models.py:1015](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1015)

   Trigger: response bytes `b"a\r\nb\r\n"` processed with `chunk_size=2`, producing chunks `b"a\r"`, `b"\nb"`, and `b"\r\n"`.

   **Expected:** `[b"a", b"b"]`, independent of chunk boundaries.

   **Code-derived result:** `[b"a", b"", b"b"]`. The first chunk’s `splitlines()` treats its trailing `\r` as a complete line ending. The implementation retains no pending carriage return, so the next chunk’s leading `\n` becomes another line ending and emits an empty line.

   This affects consumers that count records or treat blank lines as separators. Cached responses have the same problem: `iter_content()` delegates to `utils.iter_slices()` (`models.py:963–966`), so changing the requested chunk size can change the logical lines returned. The existing line-iteration test (`tests/test_requests.py:2136`) does not exercise split CRLF boundaries.

3. **[P2] Pickling a response breaks its public `.next` property** — [models.py:824](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L824)

   **Expected:** After a pickle round trip, `.next` returns the next prepared redirect request or `None`.

   **Code-derived result:** Access raises `AttributeError` because `_next` is missing. `__getstate__()` serializes only `__attrs__`, which excludes `_next` (`models.py:750–761,816–822`). Unpickling bypasses `__init__()`, and `__setstate__()` does not restore `_next`. The property directly reads it at line 892.

   Consequently, even an ordinary nonredirect response loses a previously valid `.next == None` access. Redirect responses additionally lose the prepared follow-up request stored by `Session.send()` (`sessions.py:817–822`). Existing pickle coverage checks the restored request’s URL and headers, but never `.next` (`tests/test_requests.py:1520–1530`).

**Open leads and verification limits:** Server-specific consequences of the framing defect remain unverified; no request-smuggling or particular server failure is claimed. Review used six read-only tool calls within the supplied workspace. No files were modified, external services accessed, or runtime tests—including integration tests—run.