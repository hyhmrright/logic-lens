<!-- run 4b468e5a70b0462cb3cf0b0b0bea4ee1; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Partial review of `src/requests/models.py`: `PreparedRequest.prepare_body`, `Response.iter_content`, and `Response.iter_lines`, with targeted supporting-code reads. Other functions were not exhaustively reviewed.  
**Logic Score:** 86/100

> Two concrete defects were confirmed in isolated, in-memory execution. No files were modified or external services accessed.

## Findings

### 🟡 Warning
**[L3] — CRLF split across chunks produces a spurious empty line**

Premises: `iter_content` can split a response anywhere, including between `\r` and `\n`. `iter_lines` calls `splitlines()` on individual chunks; `splitlines()` recognizes CRLF as one line boundary when both characters are together.

Trace: [1] At [models.py:1008](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1008), reading `b"a\r\nb\r\n"` in two-byte chunks produces `b"a\r"`, `b"\nb"`, and `b"\r\n"`. [2] At line 1018, the first chunk yields `b"a"`; no state remembers its terminating CR. [3] The next chunk splits into `[b"", b"b"]`; lines 1020–1025 retain `b"b"` as pending and yield the spurious `b""`. [4] The last chunk completes `b"b"`. Rebuttal check: PASSED — neither `iter_content` nor `iter_lines` preserves a split CRLF boundary.

Divergence: **L3:** Expected `[b"a", b"b"]`; observed `[b"a", b"", b"b"]`. The same response therefore produces different logical lines depending on chunk boundaries.

Trigger:
```python
from io import BytesIO
from requests import Response

r = Response()
r.raw = BytesIO(b"a\r\nb\r\n")
assert list(r.iter_lines(chunk_size=2)) == [b"a", b"b"]
```
The assertion fails on the original method.

Remedy: Initialize `skip_lf = False` before `pending`. Insert this block immediately inside the chunk loop, before pending concatenation:

```python
if not chunk:
    continue
if not delimiter:
    lf = "\n" if isinstance(chunk, str) else b"\n"
    cr = "\r" if isinstance(chunk, str) else b"\r"
    if skip_lf and chunk.startswith(lf):
        chunk = chunk[1:]
    skip_lf = False
    if not chunk:
        continue
    skip_lf = chunk.endswith(cr)
```

Dry-run: ✅ A CR still terminates its line immediately; its following LF is consumed once. Standalone CR, LF, empty input, and existing custom-delimiter handling are preserved.

Verification: ✅ Execution-verified using extracted methods and in-memory streams: original assertion FAIL → remedy PASS. The remedy also passed 28 byte-input boundary comparisons against `bytes.splitlines()` and a Unicode CRLF case.

### 🟡 Warning
**[L6] — Generated transfer encoding disagrees with the adapter’s framing decision**

Premises: A caller can supply a correct `Content-Length` for an iterator whose length Requests cannot discover. Header preparation validates header syntax without rejecting that combination. `HTTPAdapter.send` determines its `chunked` argument from the presence of `Content-Length`.

Trace: [1] `prepare_body` receives `iter([b"abc"])` and headers `{"Content-Length": "3"}`. [2] At [models.py:603](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L603), local `utils.super_len` returns zero because the iterator exposes no length or position. [3] Lines 625–628 add `Transfer-Encoding: chunked` without removing or honoring the existing length header. [4] At [adapters.py:679](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/adapters.py#L679), the existing `Content-Length` makes `chunked=False`; both headers are passed to `conn.urlopen`. Rebuttal check: PASSED — the default adapter’s `add_headers` is a no-op, and the inspected path contains no reconciliation.

Divergence: **L6:** Expected consistent framing—here, the supplied three-byte length without an automatically added chunked header. Observed preparation produces both headers, while the adapter selects `chunked=False`. This contradictory state is confirmed; final wire bytes and server behavior remain unverified.

Trigger:
```python
from requests import Request

p = Request(
    "POST", "http://example.invalid/",
    data=iter([b"abc"]),
    headers={"Content-Length": "3"},
).prepare()

assert not (
    "Content-Length" in p.headers
    and "Transfer-Encoding" in p.headers
)
```
Observed headers include both `Content-Length: 3` and `Transfer-Encoding: chunked`.

Remedy: At `models.py:627`, replace the `else:` immediately preceding the transfer-encoding assignment with:

```python
elif "Content-Length" not in self.headers:
```

Dry-run: ✅ The trigger retains its explicit length and gains no conflicting header. Unknown-length iterators without an explicit length retain chunked encoding; the known-length branch is unchanged.

Verification: ✅ Execution-verified for the iterator trigger: original assertion FAIL → remedy PASS. The ordinary unknown-length iterator check also passed. Additional file-like-stream checks stopped because the isolated harness omitted its `io` binding; those extended checks remain unverified.

## Summary

Both findings have concrete observable consequences: an extra empty line and contradictory request-framing metadata. The proposed edits were evaluated only in memory; source files remain unchanged.

**Open leads and verification limits:** Dependency-level serialization and server handling of the contradictory headers remain open questions, not established failures. No package-level integration tests or network tests were run, and the remaining functions in `models.py` were not exhaustively reviewed.