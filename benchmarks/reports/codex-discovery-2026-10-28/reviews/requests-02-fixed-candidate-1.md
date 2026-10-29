<!-- run dbc7a3a2b3804d68b253e7718398f113; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces of `src/requests/models.py`: request-body framing, `iter_content()`, and `iter_lines()`, supported by utilities, adapters, session callers, tests, and documentation. URL, authentication, cookies, and serialization were not exhaustively traced. Ten shell calls used; no files changed.  
**Logic Score:** 86/100

> Two defects are supported by complete static traces. Runtime reproduction and integration testing were excluded by the requested protocol.

## Findings

### 🟡 Warning

**[L3] — Splitting CRLF across chunks introduces a nonexistent blank line**

**Premises:** `iter_lines()` promises to return response data one line at a time (`models.py:996`). The existing test expects four response lines to produce four iterator items (`tests/test_requests.py:2136`). Its supported file-like response path reads chunks using `raw.read(chunk_size)` (`models.py:949`); chunk boundaries need not coincide with line boundaries.

**Trace:**

1. For `raw = io.BytesIO(b"a\r\nb\r\n")` and `chunk_size=2`, `iter_content()` yields `b"a\r"`, `b"\nb"`, and `b"\r\n"`.
2. At [models.py:1018](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L1018), `b"a\r".splitlines()` produces `[b"a"]`. The trailing `\r` is discarded; `pending` becomes `None`.
3. The next chunk, `b"\nb"`, splits into `[b"", b"b"]`. The code retains `b"b"` as pending and emits `b""`.
4. The final chunk completes `b"b\r\n"` and emits `b"b"`.

Rebuttal check: Unicode decoding handles encoded-character boundaries (`utils.py:603`), but no preceding step joins CRLF across chunks. The documented restriction on reentrant iteration does not apply to this single iterator.

**Divergence:** **L3** at `models.py:1018–1023`: processing each chunk independently loses the fact that a trailing CR and subsequent LF constitute one line ending. The statically derived result is `[b"a", b"", b"b"]`; the response contains only the two lines `a` and `b`. Consumers receive a fabricated blank record.

**Trigger:**

```python
r = requests.Response()
r.raw = io.BytesIO(b"a\r\nb\r\n")
list(r.iter_lines(chunk_size=2))
# Expected: [b"a", b"b"]
# Derived actual: [b"a", b"", b"b"]
```

**Remedy:** After initializing `pending`, add `skip_lf = False`. Inside the chunk loop, immediately before `if pending is not None:`, insert:

```python
if not delimiter and chunk:
    lf = "\n" if isinstance(chunk, str) else b"\n"
    cr = "\r" if isinstance(chunk, str) else b"\r"
    if skip_lf and chunk.startswith(lf):
        chunk = chunk[1:]
    skip_lf = chunk.endswith(cr)
```

Dry-run: this suppresses only the LF belonging to a preceding CR. LF-only input, standalone CR, and genuine consecutive blank lines remain intact. Explicit-delimiter handling is unchanged. These checks were mental traces.

**Verification:** ⚠️ Unverified by execution. The result follows the actual file-like read and splitting branches; no runtime test or remedy test was run.

### 🟡 Warning

**[L6] — Generator preparation adds chunked framing despite an explicit length**

**Premises:** Generator request bodies are supported (`docs/user/advanced.rst:371`). Custom headers are preserved when their values cannot be determined automatically (`docs/user/quickstart.rst:228–230`). Existing framing tests explicitly require avoiding simultaneous `Content-Length` and `Transfer-Encoding` (`tests/test_requests.py:2210–2232`).

**Trace:**

1. Prepare a POST with `data=(part for part in [b"abc"])` and `headers={"Content-Length": "3"}`. Header preparation retains the supplied, correct length.
2. The generator enters the streaming branch at `models.py:601`. `utils.super_len()` cannot measure it and returns `0` (`utils.py:225–228`).
3. At [models.py:625](https://github.com/psf/requests/blob/6404f345e562d962abe6700a1c357ec1e7e18232/src/requests/models.py#L625), the false length selects the branch adding `Transfer-Encoding: chunked`, without removing or checking `Content-Length`.
4. At [adapters.py:679](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/adapters.py#L679), the adapter sees `Content-Length` and selects `chunked=False`. Both headers and that flag are passed to `conn.urlopen()`.

Rebuttal check: preparation without an authenticator performs no subsequent framing correction. The existing generator test supplies no explicit length, so it does not cover this combination.

**Divergence:** **L6** at `models.py:628`, interacting with `adapters.py:679`: preparation declares chunked transfer encoding while the adapter selects sending by content length. The confirmed consequence is a prepared request containing contradictory framing headers and inconsistent adapter options. Whether a server rejects or misinterprets the request depends on downstream behavior and was not established.

**Trigger:**

```python
p = requests.Request(
    "POST",
    "http://example.invalid/",
    data=(part for part in [b"abc"]),
    headers={"Content-Length": "3"},
).prepare()
```

Expected: retain `Content-Length: 3` without automatically adding chunked encoding. Derived actual: both `Content-Length: 3` and `Transfer-Encoding: chunked`.

**Remedy:** Replace the `else:` at `models.py:627` with:

```python
elif "Content-Length" not in self.headers:
```

Keep the existing assignment beneath it. Dry-run: the trigger retains only its supplied length; generators without a supplied length still receive chunked encoding; measurable nonempty bodies retain their existing length calculation. This specifically prevents the automatically introduced conflict.

**Verification:** ⚠️ Static evidence only. Neither request transmission nor the proposed remedy was executed. Downstream HTTP handling was not assumed as evidence.

## Summary

The confirmed defects affect line-stream contents and request-framing consistency. Both remedies are localized, but remain untested. The score deducts seven points per confirmed finding and describes only the inspected paths—not whole-module correctness or shipping readiness.

## Unresolved Investigations

- **Explicit port zero:** `prepare_url()` reconstructs the port only when it is truthy (`models.py:539`). If `urllib3.parse_url()` returns integer `0` for an accepted explicit `:0`, preparation would discard it. The relevant dependency implementation and acceptance contract were unavailable within the supplied workspace, so this remains a lead. The next check is to inspect that dependency’s parsing contract and establish the expected prepared URL; it does not affect the score.