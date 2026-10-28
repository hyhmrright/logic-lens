<!-- run 5f9a4b5e3dce44fba334d7a9819d6661; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Deep traces of `PreparedRequest.prepare_body` and `Response.iter_lines` in `src/requests/models.py`, with supporting callers, helpers, types, documentation, and tests. Other functions were not exhaustively reviewed.  
**Logic Score:** 86/100

> Two concrete defects reproduced in isolated computations: an incorrect request-body length and chunk-dependent extra empty lines.

## Findings

### 🟡 Warning
**[L6] — Sized iterable bodies use chunk count as byte length**

Premises: The declared `DataType` accepts `Iterable[bytes | str]`. A `deque([b"ab", b"cd"])` satisfies that contract, but its length is **two elements**, containing **four bytes**. [`super_len`](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/utils.py#L169) returns `len(o)` when available.

Trace: [1] [`prepare_body:600`](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L600) classifies the deque as a streamed body. [2] At line 603, `super_len(data)` returns integer `2`. [3] Lines 607 and 626 retain the original four-byte iterable and set `Content-Length: 2`. [4] [`HTTPAdapter.send:679`](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/adapters.py#L679) selects non-chunked sending because that header exists. Rebuttal check: PASSED — the input is admitted by the local type contract; no upstream restriction or downstream correction was found in the inspected path.

Divergence: **L6:** `prepare_body` assumes `super_len` measures serialized bytes for every iterable. The observed prepared header is `Content-Length: 2`, while joining the retained body produces `b"abcd"`—four bytes. Correct framing requires length `4` or chunked encoding. Server handling of this mismatch was not tested.

Trigger:
```python
from collections import deque
p = requests.Request(
    "POST", "http://example.test/", data=deque([b"ab", b"cd"])
).prepare()
# Expected: Content-Length 4, or chunked without Content-Length
# Actual:   Content-Length 2
```

Remedy: Immediately inside the stream branch, before calculating `length`, normalize non-readable, non-buffer iterables into iterators:
```python
if not isinstance(data, (bytearray, memoryview)) and not hasattr(data, "read"):
    data = iter(data)
```
The iterator then has unknown length, so preparation selects chunked encoding. This also prevents authentication’s later length recalculation from restoring the erroneous element count. Dry-run: ✅ The trigger retains all four bytes; ordinary generators remain chunked, and `BytesIO(b"abcd")` retains length `4`.

Verification: ✅ Execution-verified — extracted original functions failed the byte-length assertion; the in-memory remedy passed. Transport integration remains unverified.

### 🟡 Warning
**[L3] — Line parsing invents empty records at chunk boundaries**

Premises: [`iter_content`](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L915) provides chunks rather than complete lines. Identical response bytes can therefore reach `iter_lines` under different chunk partitions. `bytes.split(b"\n")` retains a trailing empty component; `splitlines()` treats both CR and CRLF as line endings.

Trace: [1] At [`iter_lines:1016`](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1015), chunk `b"a\n"` with delimiter `b"\n"` becomes `[b"a", b""]`. [2] Line 1020’s truthiness check rejects that empty final component as pending data. [3] Line 1025 immediately yields both elements; the next chunk `b"b"` eventually yields `b"b"`. [4] Separately, default parsing of chunks `[b"a\r", b"\nb"]` recognizes CR and LF independently, again yielding an extra empty line. Rebuttal check: PASSED — neither path requires reentrant use, no chunk-alignment guarantee exists, and `iter_lines` itself does not remove the invented record.

Divergence: **L3:** The observed result is `[b"a", b"", b"b"]`; the expected result is `[b"a", b"b"]`. Supplying the same bytes in one chunk produces the expected result. Consumers therefore receive records whose existence depends on chunk boundaries.

Trigger: With `iter_content` yielding the specified chunks:

| Chunks | Delimiter | Expected | Observed |
|---|---|---|---|
| `[b"a\n", b"b"]` | `b"\n"` | `[b"a", b"b"]` | `[b"a", b"", b"b"]` |
| `[b"a\r", b"\nb"]` | Default | `[b"a", b"b"]` | `[b"a", b"", b"b"]` |

Remedy: Replace the method’s implementation body with:
```python
pending = None
skip_lf = False
for chunk in self.iter_content(
    chunk_size=chunk_size, decode_unicode=decode_unicode
):
    if not chunk:
        continue
    cr, lf = (
        ("\r", "\n") if isinstance(chunk, str)
        else (b"\r", b"\n")
    )
    if not delimiter and skip_lf and chunk.startswith(lf):
        chunk = chunk[1:]
    skip_lf = not delimiter and chunk.endswith(cr)

    if pending is not None:
        chunk = pending + chunk

    if delimiter:
        lines = chunk.split(delimiter)
        pending = lines.pop()
    else:
        lines = chunk.splitlines()
        if lines and lines[-1] and chunk and lines[-1][-1] == chunk[-1]:
            pending = lines.pop()
        else:
            pending = None
    yield from lines

if pending:
    yield pending
```
Dry-run: ✅ Both triggers return two records. Checks across every single-cut partition of selected empty, ordinary, blank-line, CRLF, and multicharacter-delimiter payloads passed for bytes and Unicode strings.

Verification: ✅ Execution-verified — the original extracted method failed both boundary assertions; the in-memory replacement passed.

## Summary

The body-length defect warrants priority because the prepared header disagrees with the retained payload. Line iteration also needs correction so response chunking cannot create records.

**Open lead, excluded from findings and score:** Unicode text-stream lengths merit further investigation: `super_len` measures `StringIO` positions in characters, while transmitted length depends on encoding. Documentation already warns about text-mode uploads; transport behavior was not established here.

Verification used AST-extracted workspace functions with in-memory harnesses. No source files were modified, no external services were accessed, and no runtime integration tests ran. These results establish the local divergences, not end-to-end server consequences.