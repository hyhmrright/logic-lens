<!-- run a0b849bb505343728ce024c3811278ad; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Deep review of `PreparedRequest.prepare_body`, `Response.iter_content`, and `Response.iter_lines`, with supporting helpers, redirect handling, and tests. Remaining functions were not exhaustively reviewed.  
**Logic Score:** 86/100

Three concrete defects follow from source traces. No code was executed, so the consequences below are source-derived, not runtime observations. No files were modified or external services accessed.

## Findings

### 🟡 Warning
**[L3] — Line splitting inserts empty records at chunk boundaries**

Premises: `iter_lines()` consumes arbitrary chunks from `iter_content()`. Chunk boundaries should not change the logical lines. Both bytes and decoded strings are supported.

Trace: [1] At [models.py:1018](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1018), chunk `b"a\r"` becomes `[b"a"]`. [2] Lines 1020–1023 retain no pending data because `b"a"` and `b"a\r"` end differently. [3] The next chunk, `b"\nb"`, becomes `[b"", b"b"]`; the empty line is emitted. Explicit delimiters have a related failure: splitting chunk `b"a|"` on `b"|"` immediately emits its trailing empty fragment, even when the next chunk continues that record. Rebuttal check: PASSED — no boundary reconciliation exists; the existing line-iteration test at `tests/test_requests.py:2136` does not exercise these splits.

Divergence: **L3:** `b"a\r\nb"` produces `[b"a", b"", b"b"]` with two-byte chunks, instead of `[b"a", b"b"]`. Likewise, `b"a|b"` with delimiter `b"|"` produces an extra empty record with two-byte chunks. Consumers receive records absent from the response.

Trigger: These are reproduction recipes, not executed results:

```python
from requests import Response

r = Response()
r._content = b"a\r\nb"
r._content_consumed = True
list(r.iter_lines(chunk_size=2))
# Expected: [b"a", b"b"]
# Source-derived actual: [b"a", b"", b"b"]

r._content = b"a|b"
list(r.iter_lines(chunk_size=2, delimiter=b"|"))
# Expected: [b"a", b"b"]
# Source-derived actual: [b"a", b"", b"b"]
```

Remedy: Replace lines 1006–1028 with the following, retaining a possible CRLF boundary and deferring the final explicit-delimiter fragment:

```python
pending = None
for chunk in self.iter_content(
    chunk_size=chunk_size, decode_unicode=decode_unicode
):
    if pending is not None:
        chunk = pending + chunk

    if delimiter:
        lines = chunk.split(delimiter)
        pending = lines.pop()
        yield from lines
    else:
        lines = chunk.splitlines(keepends=True)
        pending = None
        if lines:
            last = lines[-1]
            cr = "\r" if isinstance(last, str) else b"\r"
            if last.endswith(cr) or last.splitlines() == [last]:
                pending = lines.pop()
        for line in lines:
            yield line.splitlines()[0]

if pending is not None:
    if delimiter:
        yield pending
    else:
        yield from pending.splitlines()
```

Dry-run: Both triggers yield two records; ordinary LF lines, empty lines, terminal CR, and bytes/string handling remain intact.

Verification: ⚠️ Unverified — static tracing only; neither reproducer nor replacement was executed.

### 🟡 Warning
**[L6] — Non-iterable file-like bodies are not rewound for redirects**

Premises: `SupportsRead` is an accepted body type independently of `Iterable` (`_types.py:98–105`). A file-like object can expose `read`, `tell`, and `seek` without exposing `__iter__`. A 307/308 redirect preserves the request body.

Trace: [1] At [models.py:599](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L599), such an object bypasses the iterable branch, including its `_body_position` assignment. [2] `_encode_params()` returns the readable object unchanged at lines 164–165; `prepare_content_length()` computes its remaining length through `utils.super_len()`. `_body_position` stays `None`. [3] After transmission consumes the object, `PreparedRequest.copy()` preserves the same body reference and missing position. [4] [sessions.py:278](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/sessions.py#L278) consequently skips `rewind_body()` before resending. Rebuttal check: PASSED — the declared input contract permits this object; redirect handling supplies no alternative rewind. Existing rewind tests use iterable objects.

Divergence: **L6:** Redirect handling assumes preparation recorded the starting position of a seekable body. For this supported input, the redirected request instead retains an exhausted body and the original nonzero `Content-Length`. Its next read returns no payload. A receiver waiting for the advertised bytes can stall; that network consequence was not tested.

Trigger:

```python
from io import BytesIO
from requests import Request

class Body:
    def __init__(self):
        buf = BytesIO(b"abc")
        self.read = buf.read
        self.tell = buf.tell
        self.seek = buf.seek

p = Request("POST", "https://example.invalid/start", data=Body()).prepare()
p.body.read()  # Simulate initial transmission: b"abc"
```

Then follow a 307 or 308 to `/next`. Expected: rewind to position zero and resend `b"abc"`. Source-derived actual: `_body_position is None`, rewind is skipped, and the redirected body reads `b""` despite `Content-Length: 3`.

Remedy: Immediately before `self.body = body` at line 650, insert:

```python
if self._body_position is None and getattr(body, "tell", None) is not None:
    try:
        self._body_position = body.tell()
    except OSError:
        self._body_position = object()
```

Dry-run: The trigger records position zero, enabling the existing redirect rewind. Already-recorded iterable positions remain unchanged; byte/string bodies bypass the addition.

Verification: ⚠️ Unverified — static tracing only; redirect transmission and remedy were not executed.

### 🟡 Warning
**[L3] — Zero-size iteration falsely consumes an unread response**

Premises: `iter_content()` accepts integer chunk sizes without a positivity check. The cached-content helper explicitly treats zero as “return all remaining content” (`utils.py:626–627`). Standard file-like raw responses are supported and exercised in `tests/test_requests.py:1455–1459`.

Trace: [1] At [models.py:958](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L958), zero passes validation. [2] With a `BytesIO` raw body, line 949 calls `read(0)`, obtaining `b""` without advancing its position. [3] Line 951 interprets this as EOF, and line 954 sets `_content_consumed = True`. [4] Subsequent `.content` access raises at line 1037 because `_content` is still `False`. Rebuttal check: PASSED — no guard prevents zero; the cached path handles it differently.

Divergence: **L3:** Iteration returns no bytes and permanently marks the response consumed even though all bytes remain unread. Later `.content` access raises `RuntimeError`.

Trigger:

```python
from io import BytesIO
from requests import Response

r = Response()
r.status_code = 200
r.raw = BytesIO(b"abc")
list(r.iter_content(0))
# Source-derived actual: []; raw position remains 0
r.content
# Source-derived actual: RuntimeError
```

Expected: return the content consistently with cached iteration, or reject zero without changing consumption state.

Remedy: After the existing type check and before line 963, insert:

```python
if chunk_size == 0:
    chunk_size = None
```

Dry-run: `BytesIO.read(None)` reads `b"abc"` before EOF is recorded. Cached zero-size behavior remains equivalent, and positive sizes are unchanged.

Verification: ⚠️ Unverified — static tracing only; reproducer and remedy were not executed.

## Summary

Prioritize redirect replay and line-boundary handling. The score deducts seven points per unique risk code, so the two L3 findings share one deduction.

An **open lead, not a confirmed finding or scored deduction**, is non-ASCII `StringIO` length handling: `super_len()` measures stream positions, while transport encoding may expand characters into multiple bytes. The resulting wire behavior depends on dependency behavior that was not verified within this workspace-only review.