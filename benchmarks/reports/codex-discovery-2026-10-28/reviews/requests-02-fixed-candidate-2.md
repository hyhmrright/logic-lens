<!-- run 45f20ce4621945c8af1e3b07437c66f8; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/models.py`, with deeper traces of body preparation and response line iteration. Supporting evidence: `utils.py`, `_types.py`, adapters, sessions, relevant tests and documentation. Other paths received a lighter review. Seven tool calls used; no files modified or runtime tests executed.  
**Logic Score:** 86/100

Two defects are supported by static traces. Their runtime and transport consequences remain untested under the requested protocol.

## Findings

### 🟡 Warning — [L6] Buffer element counts become incorrect Content-Length values

**Premises:** `DataType` explicitly accepts buffer objects in [_types.py](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/_types.py#L98). Content-Length must count bytes; `tests/test_requests.py:3037` explicitly checks byte counts rather than character counts. A contiguous `memoryview(b"abcd").cast("H")` contains four bytes but has two elements.

**Trace:**

1. `Request("POST", "https://example.test/", data=view).prepare()` reaches `PreparedRequest.prepare_body`.
2. At [models.py:601](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L601), the iterable memoryview enters the streamed-body branch.
3. `super_len(view)` resolves to [utils.py:160](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/utils.py#L160), where `len(view)` returns **2**, its element count.
4. `prepare_body` retains the four-byte view as `body` and sets `Content-Length: 2` at line 626.

Rebuttal check: the adapter forwards the body and headers and disables chunked framing when Content-Length exists (`adapters.py:679–709`). No correction appears along that inspected path.

**Divergence:** **L6 — Callee Contract Mismatch.** `prepare_body` uses `super_len` as a byte count, but it returns an element count for this buffer. The prepared request advertises **2 bytes for a 4-byte body**. This header mismatch is established statically; transmission behavior was not verified.

**Trigger:**

```python
view = memoryview(b"abcd").cast("H")
p = requests.Request(
    "POST", "https://example.test/", data=view
).prepare()
```

Expected: `p.headers["Content-Length"] == "4"`.  
Actual by trace: `"2"`.

**Remedy:** In `utils.py`, replace the `__len__` branch at lines 169–170 with:

```python
if hasattr(o, "__len__"):
    try:
        total_length = memoryview(o).nbytes
    except TypeError:
        total_length = len(o)
```

Dry-run, by reasoning only: the trigger returns 4; ordinary bytes retain their byte length, and non-buffer collections retain the existing `len` behavior.

**Verification:** ⚠️ Unverified by execution — static evidence only. Runtime integration and remedy tests were excluded by the review protocol.

### 🟡 Warning — [L3] A CRLF split across chunks creates a phantom empty line

**Premises:** `Response.iter_lines` promises response data “one line at a time” ([models.py:996](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L996)). With its default `splitlines()` semantics, `b"a\r\nb\r\n"` contains two lines. Chunk boundaries should not introduce another line.

**Trace:**

1. For a buffered response, `iter_content(2)` calls `utils.iter_slices` (`models.py:963–966`; `utils.py:621–630`), yielding `b"a\r"`, `b"\nb"`, and `b"\r\n"`.
2. At [models.py:1018](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1018), `b"a\r".splitlines()` produces `[b"a"]`. The code yields `b"a"` and retains no indication of the trailing CR.
3. `b"\nb".splitlines()` produces `[b"", b"b"]`. The code stores `b"b"` as pending and **yields `b""`**.
4. The final chunk completes and yields `b"b"`.

Rebuttal check: the Unicode decoder preserves CR/LF boundaries; it does not combine them. The buffered path also establishes reachability without assumptions about urllib3 chunk scheduling.

**Divergence:** **L3 — Boundary Blindspot.** Processing CR and LF independently across chunks turns one CRLF separator into two separators. Expected output is `[b"a", b"b"]`; actual output by trace is `[b"a", b"", b"b"]`. Consumers receive a blank line absent from the response.

**Trigger:** For a buffered response whose body is `b"a\r\nb\r\n"`, call:

```python
list(r.iter_lines(chunk_size=2))
```

**Remedy:** Add `skip_lf = False` immediately after `pending` initialization. Insert this block immediately before `if pending is not None:`:

```python
if not delimiter and chunk:
    lf = "\n" if isinstance(chunk, str) else b"\n"
    cr = "\r" if isinstance(chunk, str) else b"\r"
    if skip_lf and chunk.startswith(lf):
        chunk = chunk[1:]
    skip_lf = chunk.endswith(cr)
    if not chunk:
        continue
```

Dry-run, by reasoning only: the LF following a previous chunk’s CR is consumed once. Ordinary LF lines, genuine blank lines, lone CR separators, and explicitly supplied delimiters retain their existing handling.

**Verification:** ⚠️ Unverified by execution — static evidence only. Neither the reproduction nor the proposed remedy was executed.

## Summary

The inspected paths contain an incorrect Content-Length calculation for typed buffers and chunk-dependent line parsing for CRLF responses. The score reflects these confirmed findings within this slice, not whole-project correctness or shipping safety.

## Unresolved Investigations

- **Explicit port zero:** `prepare_url` appends the parsed port only when truthy (`models.py:539`). Potential consequence: silently dropping an explicitly supplied `:0`. Parser behavior and the supported outcome for that input were not established from workspace evidence. Next check: inspect the selected parser’s handling and adapter behavior in an authorized environment. This lead is excluded from findings and scoring.