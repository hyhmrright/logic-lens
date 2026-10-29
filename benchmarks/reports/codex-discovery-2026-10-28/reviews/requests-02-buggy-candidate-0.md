<!-- run 0e859127301442db9ad4d60ec3433652; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces of request-body preparation and response line iteration in `src/requests/models.py`, supported by callers, utilities, types, documentation, and tests. Six tool calls; no modifications, external access, or runtime tests. URL normalization and other paths were not exhaustively investigated.  
**Logic Score:** 86/100

Two defects are supported by static traces. The score describes confirmed findings within this scope, not whole-project correctness.

## Findings

### 🟡 Warning
**[L3] — Line iteration emits extra records at chunk boundaries**

Premises: `iter_lines()` promises to yield response data one line at a time (`models.py:996`). Its input chunks can split anywhere: `iter_content()` reads the requested byte count or slices cached content through `utils.iter_slices` (`models.py:949,966`; `utils.py:621–630`). Line content should therefore be independent of chunk size.

Trace:

1. For a body `b"a\r\nb"`, `iter_content(chunk_size=2)` supplies `b"a\r"` followed by `b"\nb"`.
2. At [models.py:1018](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1018), the first chunk’s `splitlines()` returns `[b"a"]`. The code yields it and retains no pending state.
3. The second chunk’s `splitlines()` returns `[b"", b"b"]`. The code yields the empty record and eventually `b"b"`.
4. The explicit-delimiter branch has a related failure: `b"a\nb"` split into `b"a\n"` and `b"b"`, with `delimiter=b"\n"`, yields `[b"a", b"", b"b"]` because the first split’s trailing empty segment is emitted immediately.

Rebuttal check: The pending-tail guard does not preserve a trailing CR or defer an empty delimiter tail. Existing tests at `tests/test_requests.py:2136` count streamed lines but do not exercise these boundaries.

Divergence: **L3** at `models.py:1015–1025`: transport chunk boundaries become observable as extra empty lines. For `b"a\r\nb"`, the expected result is `[b"a", b"b"]`; the traced result is `[b"a", b"", b"b"]`. Consumers can count nonexistent records or attempt to parse an empty record.

Trigger: A response containing `b"a\r\nb"` consumed using `list(r.iter_lines(chunk_size=2))`. Alternatively, consume `b"a\nb"` using `chunk_size=2, delimiter=b"\n"`.

Remedy: After the `pending` initialization, add:

```python
skip_lf = False
```

Replace lines 1015–1018 with:

```python
if delimiter:
    lines = chunk.split(delimiter)
    pending = lines.pop()
    yield from lines
    continue

if not chunk:
    continue

lf, cr = (b"\n", b"\r") if isinstance(chunk, bytes) else ("\n", "\r")
if skip_lf and chunk.startswith(lf):
    chunk = chunk[1:]
skip_lf = chunk.endswith(cr)
if not chunk:
    continue

lines = chunk.splitlines()
```

Keep the existing pending-tail handling and EOF flush. This preserves a possible CRLF continuation and defers explicit-delimiter tails until another chunk or EOF. **Dry-run:** Mental traces cover both triggers, unbroken CRLF, consecutive blank lines, and delimiters spanning chunks; no remedy execution was performed.

Verification: **Unverified by execution — static evidence only.** Runtime integration tests were excluded by the requested protocol.

### 🟡 Warning
**[L5] — Ignored JSON can prevent a valid multipart upload**

Premises: The request contract says `json` applies when files or data are absent (`models.py:295`). The public documentation explicitly states that JSON is ignored when `files` is supplied (`docs/user/quickstart.rst:303`). Nonempty file mappings are supported by `_encode_files()` and existing upload tests.

Trace:

1. `Request("POST", ..., files={"f": ("a.txt", b"ok")}, json={"n": float("nan")})` stores the files and defaults omitted data to an empty list (`models.py:335–350`).
2. `Request.prepare()` forwards both values into `PreparedRequest.prepare_body()` (`models.py:361–367,442`).
3. At [models.py:586](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L586), `not data and json is not None` is true, despite the nonempty files mapping.
4. `complexjson.dumps(..., allow_nan=False)` rejects NaN, and the handler raises `InvalidJSONError` at line 594. Execution never reaches multipart preparation at line 635.

Rebuttal check: The file branch would overwrite successfully serialized JSON, but cannot intercept this earlier exception. `tests/test_requests.py:2853–2856` corroborates NaN rejection for actual JSON requests; it does not cover JSON that should be ignored.

Divergence: **L5** at `models.py:592–594`: processing an unused parameter exits preparation before the required multipart body is built. Expected behavior is successful multipart preparation containing `a.txt`; the traced behavior is `InvalidJSONError`, so no upload is sent.

Trigger:

```python
requests.Request(
    "POST",
    "https://example.test/upload",
    files={"f": ("a.txt", b"ok")},
    json={"n": float("nan")},
).prepare()
```

Remedy: Replace line 586 with:

```python
if not data and not files and json is not None:
```

**Dry-run:** The trigger reaches `_encode_files()`. JSON-only NaN requests still raise, ordinary JSON requests still serialize, and nonempty form data retains precedence. These are mental checks.

Verification: **Unverified by execution — static evidence only.** Serializer selection was traced through `compat.py:64–76`; no runtime tests were run.

## Summary

The confirmed defects can introduce nonexistent response records and reject otherwise valid multipart uploads. Both have concrete, localized remedies, but neither reproduction nor remedy was executed under this discovery protocol.

## Unresolved Investigations

**U1 — Buffer byte-length accounting.** `_types.DataType` includes buffers, while `utils.super_len()` uses `len()`, which counts elements for some memoryviews rather than bytes. Incorrect request framing is a possible consequence, but the supplied evidence does not establish how the selected transport sends those buffers. The next check requires the supported transport’s buffer-conversion implementation or an existing fixture covering wide-element memoryviews. This lead is excluded from findings and scoring.