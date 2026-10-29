<!-- run 698cfe32ec3540d98bc6705929565f28; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Deep traces of `prepare_body`, `iter_lines`, and `prepare_url` in `src/requests/models.py`, with supporting helpers, callers, and tests. Other methods were not exhaustively reviewed.  
**Logic Score:** 86/100

> Two defects confirmed in isolated execution: extra empty line records and conflicting request-framing headers.

## Findings

### 🟡 Warning
**[L3] — `iter_lines()` emits extra empty records at chunk boundaries**

Premises: `iter_content()` supplies chunks whose boundaries need not coincide with line endings. `iter_lines()` supports both default line splitting and explicit delimiters.

Trace: [1] At [models.py:1018](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1018), `b"a\r".splitlines()` returns `[b"a"]`; the line is yielded without retaining the trailing CR. [2] The next chunk, `b"\nb\r"`, becomes `[b"", b"b"]`, so the LF belonging to the preceding CRLF creates an extra empty record. [3] Separately, the explicit-delimiter branch at line 1016 turns `b"a\n"` into `[b"a", b""]`; lines 1020–1025 yield that trailing empty element immediately. Rebuttal check: PASSED — neither branch reconciles these boundary artifacts; the nearby line-iteration tests do not exercise these partitions.

Divergence: **L3:** Identical content produces different records depending on chunk boundaries. For `b"a\r\nb\r\n"`, expected `[b"a", b"b"]`; partitioned chunks produce `[b"a", b"", b"b", b""]`. Explicit `delimiter=b"\n"` also inserts empty records when chunks end at delimiters. Consumers receive records absent from the body.

Trigger: Supply chunks `[b"a\r", b"\nb\r", b"\n"]` with the default delimiter, or `[b"a\n", b"b\n"]` with `delimiter=b"\n"`. Both produced `[b"a", b"", b"b", b""]`.

Remedy: Replace the implementation body after the docstring with:

```python
pending = None
previous_cr = False

for chunk in self.iter_content(
    chunk_size=chunk_size, decode_unicode=decode_unicode
):
    if not delimiter and chunk:
        cr, lf = (
            (b"\r", b"\n")
            if isinstance(chunk, bytes)
            else ("\r", "\n")
        )
        if previous_cr and chunk.startswith(lf):
            chunk = chunk[1:]
        previous_cr = chunk.endswith(cr)
        if not chunk:
            continue

    if pending is not None:
        chunk = pending + chunk

    if delimiter:
        lines = chunk.split(delimiter)
        pending = lines.pop()
    else:
        lines = chunk.splitlines()
        if (
            lines and lines[-1] and chunk
            and lines[-1][-1] == chunk[-1]
        ):
            pending = lines.pop()
        else:
            pending = None

    yield from lines

if pending:
    yield pending
```

Dry-run: ✅ Both triggers return the expected two records; genuine empty lines, ordinary LF input, Unicode chunks, split custom delimiters, and empty input retain their expected behavior.

Verification: ✅ Execution-verified in isolation — original assertions FAIL → in-memory replacement PASS. No source files changed.

### 🟡 Warning
**[L6] — Stream preparation creates headers inconsistent with adapter framing**

Premises: Caller-supplied headers reach `prepare_body()` through `prepare_headers()`. A generator without length information makes `super_len()` return zero. The adapter selects chunked sending according to the presence of `Content-Length`.

Trace: [1] Given `headers={"Content-Length": "2"}`, header preparation preserves that value. [2] In [models.py:603](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L603), `super_len(iter([b"ab"]))` returns zero. [3] Line 628 adds `Transfer-Encoding: chunked` without removing or respecting the existing length header. [4] At [adapters.py:679](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/adapters.py#L679), the remaining `Content-Length` makes `chunked=False`. Rebuttal check: PASSED — the supplied length matches the body, session preparation forwards these inputs, and no reconciliation appears before the adapter’s selection.

Divergence: **L6:** Expected coherent framing: retain the valid supplied length without adding chunked transfer encoding. Observed headers contain both `Content-Length: 2` and `Transfer-Encoding: chunked`, while the adapter selects non-chunked sending. The confirmed consequence is an inconsistent prepared request and adapter configuration; server behavior was not verified.

Trigger:

```python
requests.Request(
    "POST",
    "http://example.invalid/",
    headers={"Content-Length": "2"},
    data=iter([b"ab"]),
).prepare()
```

The isolated preparation path produced both framing headers.

Remedy: At `models.py:627`, replace the stream branch’s `else:` with:

```python
elif "Content-Length" not in self.headers:
```

Keep its existing `Transfer-Encoding` assignment underneath. Dry-run: ✅ A supplied length remains the sole framing header; an unknown-length stream without that header still receives chunked encoding.

Verification: ✅ Execution-verified in isolation using the extracted `prepare_body()` and `super_len()`, in-memory header state, and the adapter’s selection expression. Both remedy cases passed.

## Summary

Prioritize correcting line iteration and preventing automatic addition of contradictory framing headers. Verification used only isolated computation from workspace code; no package integration tests, network requests, external services, or file modifications occurred. Wire behavior and server responses remain unverified.

### Open lead — excluded from findings and score

`prepare_url()` uses `if port:` at `models.py:539`. If its parser returns integer `0` for an explicit `:0`, reconstruction drops that port. The supplied workspace does not include the external parser implementation, so that input-to-parser-result premise remains unverified.