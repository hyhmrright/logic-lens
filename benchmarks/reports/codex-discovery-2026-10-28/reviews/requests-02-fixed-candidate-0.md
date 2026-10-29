<!-- run 7d7f024aeefe43598967d6ec19d63030; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces of `PreparedRequest.prepare_body()`, response iteration, and JSON decoding in `src/requests/models.py`; supporting callers, utilities, adapters, documentation, and tests. This is a bounded review, not exhaustive coverage.  
**Logic Score:** 86/100

Two defects are supported by static traces. No runtime tests were executed, and no files were modified.

## Findings

### 🟡 Warning — [L4] Stream preparation preserves conflicting framing headers

**Premises:** Streamed requests should not contain both `Content-Length` and `Transfer-Encoding`. Existing tests explicitly establish this invariant in `tests/test_requests.py:2210–2243`. Custom headers and generator bodies are accepted request inputs.

**Trace:**

1. `Request.prepare()` passes custom headers and body data into `PreparedRequest.prepare()`. Header preparation retains `Content-Length: 3`.
2. For `iter([b"abc"])`, `prepare_body()` selects its streamed-body branch. `utils.super_len()` finds no length, file descriptor, or position and returns `0`.
3. [models.py:625](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L625) takes the false-length branch and adds `Transfer-Encoding: chunked` without removing `Content-Length`.
4. `HTTPAdapter.send()` at `adapters.py:679` consequently selects `chunked=False`, because `Content-Length` exists, while forwarding both headers to `conn.urlopen()`.

Rebuttal check: Header validation checks syntax rather than framing consistency. The inspected session and adapter path does not remove the conflicting header.

**Divergence:** **L4** — updating the framing headers leaves stale, contradictory state. The observable prepared request contains both headers, and the adapter’s chunking flag conflicts with its `Transfer-Encoding` header. Actual server rejection or wire framing depends on downstream urllib3 behavior and was not verified.

**Trigger:**

```python
p = requests.Request(
    "POST",
    "http://example.test/",
    data=iter([b"abc"]),
    headers={"Content-Length": "3"},
).prepare()
```

Expected: one coherent framing scheme. Static result: both `Content-Length: 3` and `Transfer-Encoding: chunked`.

The inverse also occurs in this branch: a known-length stream plus a custom `Transfer-Encoding: chunked` header gains `Content-Length` without removing transfer encoding.

**Remedy:** Replace the framing block at `models.py:625–628` with:

```python
if length:
    self.headers.pop("Transfer-Encoding", None)
    self.headers["Content-Length"] = builtin_str(length)
else:
    self.headers.pop("Content-Length", None)
    self.headers["Transfer-Encoding"] = "chunked"
```

Dry-run: This restores mutual exclusion for both triggers and preserves the existing framing choices for ordinary streams. This remedy addresses the streamed-body branch.

**Verification:** Static evidence only. Neither downstream wire behavior nor the proposed remedy was executed.

### 🟡 Warning — [L3] Chunk boundaries make `iter_lines()` invent empty records

**Premises:** `iter_lines()` promises response data “one line at a time” (`models.py:996`). `iter_content()` can divide a response into arbitrary chunks; cached responses use the actual `utils.iter_slices()` implementation. Changing chunk boundaries should preserve the logical records.

**Trace:**

1. With cached content `b"a\r\nb"` and `chunk_size=2`, `iter_content()` yields `b"a\r"` followed by `b"\nb"`.
2. [models.py:1018](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1018) evaluates `b"a\r".splitlines()` as `[b"a"]`. The subsequent condition clears `pending`, and `b"a"` is yielded.
3. The next chunk is independently split into `[b"", b"b"]`. The method yields the empty record and eventually `b"b"`.
4. With `chunk_size=4`, the same body instead produces `[b"a", b"b"]`.

Explicit delimiters have a related boundary defect: with body `b"a\nb"`, `delimiter=b"\n"`, and `chunk_size=2`, `chunk.split(delimiter)` produces `[b"a", b""]`. Both entries are immediately yielded, so the result is `[b"a", b"", b"b"]`; one complete chunk produces `[b"a", b"b"]`.

Rebuttal check: Unicode decoding preserves character boundaries but does not repair line-separator state. The documented non-reentrancy restriction does not apply: each example uses one iterator.

**Divergence:** **L3** — the algorithm treats a CRLF divided between chunks as two separators and treats an explicit delimiter’s trailing split fragment as a completed record. Consumers receive extra empty records whose existence depends on chunk size.

**Trigger:** For separate response objects with `_content_consumed=True`:

| `_content` | Call | Expected | Static result |
|---|---|---|---|
| `b"a\r\nb"` | `list(r.iter_lines(chunk_size=2))` | `[b"a", b"b"]` | `[b"a", b"", b"b"]` |
| `b"a\nb"` | `list(r.iter_lines(chunk_size=2, delimiter=b"\n"))` | `[b"a", b"b"]` | `[b"a", b"", b"b"]` |

These cached-state inputs exercise the real `iter_content()` → `iter_slices()` path without assuming network scheduling.

**Remedy:** Add `skip_lf = False` beside the `pending` initialization. After concatenating `pending` and `chunk`, immediately before `if delimiter:`, insert:

```python
if not delimiter:
    if skip_lf and chunk[:1] in ("\n", b"\n"):
        chunk = chunk[1:]
    skip_lf = chunk[-1:] in ("\r", b"\r")
    if not chunk:
        continue
```

Replace the explicit-delimiter branch with:

```python
if delimiter:
    lines = chunk.split(delimiter)
    pending = lines.pop()
    yield from lines
    continue
```

Keep the existing default splitting and final pending flush.

Dry-run: The first change consumes the LF belonging to a preceding CR while preserving a subsequent independent newline. The second buffers the final split fragment until more content or EOF, including separators spanning chunks. Ordinary LF splitting remains unchanged.

**Verification:** Static evidence only. Trigger outputs and remedy behavior were traced, not executed.

## Summary

Normalize stream framing headers and preserve separator state across response chunks. The score reflects these two confirmed defects within the inspected slice; it does not establish whole-file correctness.

## Unresolved Investigations

**I1 — Short UTF-16 JSON scalars:** `models.py:1097` skips explicit UTF detection for bodies of three bytes or fewer. A BOM-less UTF-16 scalar such as `b"1\x00"` therefore reaches charset detection and text decoding. Rejection remains an open lead because the result depends on the selected detection backend; the next check is a permitted isolated probe of both supported backends. This lead does not affect the score.