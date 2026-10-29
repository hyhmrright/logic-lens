<!-- run 47f34914733246bebae0454e27897db6; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Deep review of `PreparedRequest.prepare_body` and `Response.iter_lines`; supporting caller, utility, adapter, documentation, and test reads. Preliminary inspection of `prepare_url`. Other methods were not comprehensively traced.  
**Logic Score:** 93/100

> Two concrete defects survived isolated verification. Both are L3 findings; the supplied scoring rules deduct once per risk code per module.

Verification used extracted workspace functions with in-memory inputs and stubs. No integration tests, network calls, external-service access, or source modifications occurred. Nine shell calls were used.

## Findings

### 🟡 Warning
**[L3] — Stream preparation introduces conflicting framing headers**

Premises: Callers can supply a correct `Content-Length` alongside an iterator body. Header validation checks syntax, without excluding this combination. For an iterator without length metadata, `utils.super_len` returns `0`.

Trace: [1] `prepare_headers` preserves `Content-Length: 3`. [2] `prepare_body` recognizes `iter([b"abc"])` as a stream; `super_len` returns `0`. [3] [models.py:628](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L628) adds `Transfer-Encoding: chunked` without removing or accounting for the existing length. [4] [adapters.py:679](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/adapters.py#L679) consequently selects `chunked=False`, then passes both headers to `conn.urlopen`. Rebuttal check: PASSED — the input headers are supported, preparation reaches this branch directly, and the default adapter does not reconcile the conflict.

Divergence: L3 — expected framing is `Content-Length: 3` alone. Observed prepared headers are `{"Content-Length": "3", "Transfer-Encoding": "chunked"}`, while the adapter selects non-chunked sending. The confirmed consequence is contradictory HTTP framing configuration. Server rejection, blocking, or other wire behavior was not verified.

Trigger:
```python
Request(
    "POST", "http://example.invalid/",
    data=iter([b"abc"]),
    headers={"Content-Length": "3"},
).prepare()
```
An empty `BytesIO` with supplied `Content-Length: 0` also acquires the conflicting header. Existing tests at `tests/test_requests.py:2210–2243` assert framing exclusivity for streams, but omit supplied length headers.

Remedy: At line 627, replace `else:` with:
```python
elif "Content-Length" not in self.headers:
```
Keep the existing assignment beneath it. Dry-run: ✅ Supplied lengths remain intact without adding chunked encoding; streams without supplied lengths retain their existing behavior.

Verification: ✅ Execution-verified — assertions failed against the extracted original function and passed with the in-memory remedy. Empty, unknown-length, and known-length stream checks also passed. Transport integration remains unverified.

### 🟡 Warning
**[L3] — A CRLF split between chunks creates an extra empty line**

Premises: `iter_content` exposes chunks without guaranteeing that line separators remain intact. `bytes.splitlines()` and `str.splitlines()` treat CRLF as one separator when contiguous, but each isolated CR or LF also terminates a line.

Trace: [1] For chunks `[b"a\r", b"\nb\r\n"]`, [models.py:1018](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1018) splits the first chunk into `[b"a"]`. [2] Lines 1020–1023 clear `pending` because the chunk ended in a separator; the trailing CR is forgotten. [3] The second chunk independently splits into `[b"", b"b"]`. [4] Line 1025 yields the invented empty record. Rebuttal check: PASSED — chunk boundaries permit this path, no separator state prevents it, and callers that retain empty lines observe the error. The documentation’s example filters empty lines, but the API does not enforce that workaround.

Divergence: L3 — expected lines for `b"a\r\nb\r\n"` are `[b"a", b"b"]`. Observed output is `[b"a", b"", b"b"]`. Identical content therefore produces different records depending on chunk boundaries, potentially altering record counts or blank-line protocol boundaries.

Trigger:
```python
r = Response()
r._content = b"a\r\nb\r\n"
r._content_consumed = True
list(r.iter_lines(chunk_size=2))
# Expected: [b"a", b"b"]
# Observed: [b"a", b"", b"b", b""]
```
The isolated reproducer supplied the equivalent chunk sequence directly through a stubbed `iter_content`.

Remedy: Add `skip_lf = False` immediately before the loop at line 1008. Insert this at the beginning of the loop, before pending-content concatenation:
```python
if not delimiter and chunk:
    crlf = b"\r\n" if isinstance(chunk, bytes) else "\r\n"
    if skip_lf and chunk.startswith(crlf[1:]):
        chunk = chunk[1:]
    skip_lf = chunk.endswith(crlf[:1])
    if not chunk:
        continue
```
Dry-run: ✅ A leading LF following an already-consumed CR is suppressed. Standalone CR/LF separators, real blank lines, and custom-delimiter behavior are preserved.

Verification: ✅ Execution-verified — the extracted original produced the extra record; the remedy passed 604 byte/string partition cases plus an empty-chunk check. Full response integration remains unverified.

## Summary

The confirmed defects affect stream framing and line-record accuracy under specific inputs. The proposed edits were checked only in memory; no files were changed.

**Open lead — excluded from findings and score:** `prepare_url` uses `if port:` at line 539, which would discard an integer port value of `0`. Whether the installed external URL parser accepts and returns that value was not established within the workspace-only review, so changed-destination behavior is not claimed as confirmed.