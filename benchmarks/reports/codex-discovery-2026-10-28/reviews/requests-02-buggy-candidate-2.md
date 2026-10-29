<!-- run f62bc2d7a3d449e6b4fab112d448a8bb; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/models.py`, with targeted traces through request preparation, redirect handling, length calculation, cached response iteration, documentation, and tests. Seven tool calls used. Other paths were not exhaustively traced.  
**Logic Score:** 86/100

Two defects are supported by static traces. No files were modified, and no runtime or integration tests were run.

## Findings

### 🟡 Warning
**[L6] — Seekable bodies without an iterator are not rewound for redirects**

**Premises:** File-like bodies without `__iter__` are supported: `tests/test_requests.py:841–880` supplies a `TestStream` implementing `read`, `tell`, `seek`, and `__len__`, and verifies successful uploads. Separately, `test_HTTP_307_ALLOW_REDIRECT_POST_WITH_SEEKABLE` at line 239 requires a seekable upload’s contents to survive a 307 redirect.

**Trace:**

1. Preparing that `TestStream("test")` takes the non-`Iterable` branch of `prepare_body`. `_encode_params` recognizes its `read` method and returns the stream unchanged.
2. `prepare_content_length` calls `utils.super_len`, producing `Content-Length: 4`. However, position recording exists exclusively inside the iterable branch at [models.py:609](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L609), so `_body_position` remains `None`.
3. After the first upload consumes the stream, a 307/308 redirect copies the same body reference and preserves its length header.
4. At [sessions.py:278](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/sessions.py#L278), `rewindable` evaluates false because `_body_position is None`. The exhausted stream is forwarded without calling `rewind_body`.

Rebuttal check: `super_len` obtains the current position but does not store it on the prepared request; `PreparedRequest.copy` preserves the missing position. Neither supplies the omitted rewind information.

**Divergence:** **L6**, at the preparation/redirect contract boundary: a supported, seekable body is forwarded at EOF while still advertising four bytes. Expected behavior is to replay `b"test"` from its original position. The concrete erroneous state is an exhausted body with `Content-Length: 4`; a server waiting for those bytes may stall or time out.

**Trigger:** Upload the existing test’s non-iterable `TestStream("test")`; have the first endpoint fully consume it and return a 307 or 308 redirect to another upload endpoint.

**Remedy:** Delete the position-recording block at `models.py:609–618`. Insert the following immediately before `self.body = body` at line 650, outside both preparation branches:

```python
        if getattr(body, "tell", None) is not None:
            try:
                self._body_position = body.tell()
            except OSError:
                self._body_position = object()
```

Dry-run: the custom stream records position `0`, enabling the existing redirect rewind. Ordinary bytes have no `tell`; iterable file bodies retain the existing position/sentinel behavior. These checks were mental traces only.

**Verification:** ⚠️ Unverified by execution under the requested discovery protocol. Missing position recording and skipped rewind are established statically; server-specific timeout behavior was not measured.

### 🟡 Warning
**[L3] — Line iteration creates extra empty records at chunk boundaries**

**Premises:** `iter_lines` promises to iterate response data one line at a time (`models.py:996`). Its documented streaming use appears in `docs/user/advanced.rst:529–545`. `iter_content` may partition data into small chunks; chunk boundaries do not introduce additional logical lines.

**Trace:**

1. For cached content `b"a\r\nb\r\n"`, `iter_lines(chunk_size=2)` reaches `utils.iter_slices` through `iter_content`, producing chunks `b"a\r"`, `b"\nb"`, and `b"\r\n"`.
2. At [models.py:1018](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1018), the first chunk’s `splitlines()` returns `[b"a"]`. The pending-data check clears `pending`, and `b"a"` is yielded.
3. The second chunk independently splits into `[b"", b"b"]`. It retains `b"b"` as pending and yields the empty record.
4. Combining pending data with the last chunk yields `b"b"`. Overall output is `[b"a", b"", b"b"]`; processing the same body in one chunk yields `[b"a", b"b"]`.

The explicit-delimiter branch also exposes chunk boundaries: `b"a\nb\n"` with `delimiter=b"\n"` yields `[b"a", b"", b"b", b""]` at chunk size 2, versus `[b"a", b"b", b""]` in one chunk.

Rebuttal check: `pending` preserves unfinished text, but neither a trailing CR nor an empty suffix after an explicit delimiter. The existing line test checks record count without controlling these boundaries.

**Divergence:** **L3**, in the boundary handling at lines 1015–1023: chunk-local splitting emits records absent from the underlying logical sequence. Consumers receive phantom blank lines; blank-line-delimited consumers can consequently interpret a false record boundary.

**Trigger:** A response with cached body `b"a\r\nb\r\n"` consumed using `list(r.iter_lines(chunk_size=2))`. Expected: `[b"a", b"b"]`. Statically traced actual: `[b"a", b"", b"b"]`.

**Remedy:** Replace `models.py:1015–1028` with:

```python
            if delimiter:
                lines = chunk.split(delimiter)
                pending = lines.pop()
            else:
                cr = b"\r" if isinstance(chunk, bytes) else "\r"
                lines = chunk.splitlines()
                if chunk.endswith(cr):
                    pending = lines.pop() + cr
                elif (
                    lines and lines[-1] and chunk
                    and lines[-1][-1] == chunk[-1]
                ):
                    pending = lines.pop()
                else:
                    pending = None

            yield from lines

        if pending is not None:
            if delimiter:
                yield pending
            else:
                yield from pending.splitlines()
```

Dry-run: retaining trailing CR joins a split CRLF; retaining the explicit split’s final segment prevents intermediate empty suffixes from being emitted prematurely. Mental checks covered LF, CRLF, lone CR at EOF, consecutive blank lines, unterminated final lines, and explicit trailing delimiters. No remedy tests were executed.

**Verification:** ⚠️ Static evidence only. The cached-content path is entirely traceable within the workspace; no network behavior or dependency assumptions are needed for the stated outputs.

## Summary

Prioritize recording rewind positions for every prepared readable body, then correct line-boundary bookkeeping. The score deducts seven points for each confirmed finding and describes only the inspected slice, not overall correctness or release readiness.

## Unresolved Investigations

- **Explicit port zero:** `prepare_url` reconstructs the authority using `if port:`, potentially dropping an explicitly parsed zero port. The supplied workspace does not establish the imported parser’s exact behavior or the intended zero-port policy. Next check: establish those contracts before classifying endpoint rewriting as a defect. This lead is excluded from findings and scoring.