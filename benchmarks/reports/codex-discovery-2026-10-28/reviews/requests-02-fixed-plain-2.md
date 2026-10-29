<!-- run c2647ad038f4408d94d52a68a1e0246f; model gpt-6.1-sol; only temporary source links normalized -->

Two concrete defects follow from the source. The consequences below are statically derived; I did not execute tests.

1. **[P2] `iter_lines()` emits spurious empty lines when CRLF spans chunks.**  
   In [models.py:1018](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1018), each chunk is processed with `splitlines()`. When a chunk ends with `\r`, the method yields the line and clears `pending`. It then treats the next chunk’s leading `\n` as another line ending.

   **Trigger:** A cached body of `b"a\r\nb\r\n"`, read using `list(response.iter_lines(chunk_size=1))`.

   **Expected:** `[b"a", b"b"]`.  
   **Derived actual result:** `[b"a", b"", b"b", b""]`.

   Thus, identical content produces different logical lines depending on chunk boundaries. Consumers that interpret blank lines as record separators can receive false boundaries. The existing test at `tests/test_requests.py:2136` checks a streamed line count without explicitly exercising split CRLF sequences.

2. **[P2] Deserializing a response breaks its public `next` property.**  
   The serialized attribute list in [models.py:750](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L750) omits `_next`. [Response.__setstate__ at models.py:824](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L824) restores the listed attributes but never initializes `_next`. Unpickling does not call `__init__`, where `_next` normally receives its default.

   **Trigger:** Pickle and unpickle a response, then access the restored response’s `.next`.

   **Expected:** A usable property returning `None` for a response without a pending redirect, or the preserved prepared redirect request.  
   **Derived actual result:** `AttributeError`, because the property accesses an absent `_next` attribute. A pending redirect request is also discarded.

   This affects ordinary session responses: `sessions.py:818–824` populates `_next` when redirects are disabled. The existing pickle test at `tests/test_requests.py:1520` checks the restored request’s URL and headers, but never accesses `.next`.

No additional open leads are included as findings. Verification was limited to static inspection of the supplied workspace; no runtime or integration tests, external services, or file modifications were used.