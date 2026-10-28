<!-- run e577c7350f6541b8b94a7e70ed10011b; model gpt-6.1-sol; only temporary source links normalized -->

Two defects are supported by static code paths. These are source-derived consequences, not runtime observations.

1. **Seekable bodies without `__iter__` are not rewound for redirects.**  
   In [models.py:599](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L599), recording `_body_position` is restricted to iterable bodies. A non-iterable object implementing `read`, `tell`, and `seek` instead passes through `_encode_params` unchanged, gets a content length, and retains `_body_position = None`.

   This input is explicitly supported by [test_requests.py:841](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/tests/test_requests.py#L841), which exercises a seekable stream without iteration.

   **Expected:** After a 307/308 redirect, resend the body from its original position.  
   **Actual code path:** Once the first upload consumes the body, the redirected request retains that exhausted object and its original `Content-Length`. [sessions.py:278](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/sessions.py#L278) skips rewinding because `_body_position` is `None`. The redirected upload therefore lacks the intended payload; a server waiting for the advertised bytes can stall or time out.

2. **`iter_lines()` emits spurious empty lines when CRLF crosses chunk boundaries.**  
   [models.py:1015](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1015) calls `splitlines()` on each chunk. A trailing `\r` is immediately treated as a complete line ending, leaving no pending state to absorb a leading `\n` in the next chunk.

   **Expected:** Body `b"a\r\nb\r\n"` produces `[b"a", b"b"]` regardless of chunk boundaries.  
   **Actual code trace:** With two-byte chunks—`b"a\r"`, `b"\nb"`, `b"\r\n"`—the method produces `[b"a", b"", b"b"]`. With the entire body in one chunk, it produces the expected two lines. Consumers thus receive a false blank record depending on chunk size or transport segmentation.

**Open lead:** Explicit port `0` may be discarded. [models.py:539](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L539) uses `if port:` when reconstructing the URL. If the imported parser returns integer `0` for `http://example.test:0/`, preparation drops the explicit port. The supplied workspace does not contain that parser’s implementation, so its acceptance and representation of this input remain unverified.

Verification was limited to targeted workspace source and test inspection. No tests, runtime integration checks, external services, credentials, parent directories, or history were accessed, and no files were modified. Server-side outcomes remain unobserved.