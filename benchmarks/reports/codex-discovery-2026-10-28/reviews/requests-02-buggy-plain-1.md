<!-- run e2b43d1b4aab40fbbc6c2d2f86382b85; model gpt-6.1-sol; only temporary source links normalized -->

Found two defects, both reproduced using the exact methods extracted from the supplied source.

1. **[P2] `iter_lines()` inserts empty records at chunk boundaries.**  
   [models.py:1015](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1015)

   Expected: identical response bytes produce identical lines regardless of how reads divide them.

   Observed in isolated checks:

   | Input | Chunks | Expected | Actual |
   |---|---|---|---|
   | `b"a\r\nb"` | `[b"a\r", b"\nb"]` | `[b"a", b"b"]` | `[b"a", b"", b"b"]` |
   | `b"a|b"`, delimiter `b"|"` | `[b"a|", b"b"]` | `[b"a", b"b"]` | `[b"a", b"", b"b"]` |

   For CRLF, splitting each chunk independently treats the separated `\r` and `\n` as two line endings. For an explicit delimiter, the code immediately emits the trailing empty element from a chunk ending with that delimiter. Both cases introduce records absent from the response. Consumers that interpret blank lines as record or event boundaries can therefore behave differently depending on chunking.

2. **[P2] A pickled response’s `next` property raises `AttributeError` after restoration.**  
   [Serialization state, models.py:750](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L750), [restoration, models.py:824](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L824), and [property, models.py:890](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L890).

   Expected: after a pickle round trip, accessing `next` returns a prepared redirect request or `None`.

   Observed: a response whose `next` initially returned `None` instead raised `AttributeError: 'Response' object has no attribute '_next'`.

   `_next` is omitted from `__attrs__`, and `__setstate__()` never initializes it. Unpickling bypasses `__init__()`, leaving the property’s required attribute absent. A pending redirect request is also omitted from serialization. The existing response-pickling test checks the original request’s URL and headers but does not access `next`.

No additional open lead is presented as a defect.

Verification was limited to static inspection and isolated execution of extracted methods. I did not import the complete package, run the test suite or HTTP integration tests, access external services, or modify files. These checks establish the local failures above, not end-to-end network behavior.