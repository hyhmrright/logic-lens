<!-- run a9542556c3994b1a91eb5aff26198f2a; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/models.py`; prioritized `PreparedRequest.prepare_url()`, `PreparedRequest.prepare_body()`, and `Response.iter_lines()`, with supporting source, tests, and documentation. Other methods were not exhaustively traced.  
**Logic Score:** 93/100

> One confirmed defect: line iteration can invent empty lines when CRLF crosses a chunk boundary.

## Findings

### 🟡 Warning

**[L3] — Split CRLF separators produce spurious empty lines**

Premises: `iter_content()` yields chunks without guaranteeing alignment to line endings. `iter_lines()` defaults to `splitlines()`, which recognizes CRLF as one separator when both characters occur together. Its cross-chunk state stores unfinished line content, but does not remember a terminating CR.

Trace: [1] At [models.py:1018](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1018), the first chunk, `b"a\r"`, becomes `[b"a"]`. [2] At lines 1020–1023, no unfinished content is retained because the line ends in `a` while the chunk ends in CR. The method yields `b"a"`. [3] The next chunk, `b"\nb\r"`, becomes `[b"", b"b"]`, yielding an empty line before `b"b"`. [4] A final `b"\n"` yields another empty line. Rebuttal check: PASSED — CRLF is valid line input; arbitrary chunk boundaries are permitted; no internal step merges the separated CR and LF or removes the invented lines. The documentation’s optional caller-side blank-line filter limits impact for those callers, but does not correct the returned sequence.

Divergence: **L3** at `chunk.splitlines()` and the subsequent pending-content check: the body `b"a\r\nb\r\n"` should produce `[b"a", b"b"]`. With chunks `[b"a\r", b"\nb\r", b"\n"]`, the observed result is `[b"a", b"", b"b", b""]`. Consumers receive nonexistent blank records, making parsing depend on chunk boundaries.

Trigger:
```python
from requests import Response

r = Response()
r.iter_content = lambda **_: iter([b"a\r", b"\nb\r", b"\n"])
assert list(r.iter_lines()) == [b"a", b"b"]
# Actual: [b"a", b"", b"b", b""]
```

Remedy: After the `pending` initialization at line 1006, add:
```python
        pending_cr = False
```
Immediately before `if pending is not None:` inside the loop, insert:
```python
            if not delimiter and chunk:
                lf = b"\n" if isinstance(chunk, bytes) else "\n"
                cr = b"\r" if isinstance(chunk, bytes) else "\r"
                if pending_cr and chunk.startswith(lf):
                    chunk = chunk[1:]
                pending_cr = chunk.endswith(cr)
```
This remembers a completed CR separator and suppresses its continuation LF in the next nonempty chunk. Dry-run: ✅ The trigger returns two lines; checks also preserved ordinary LF, lone CR, blank lines, empty chunks, text chunks, and explicit-delimiter behavior.

Verification: ✅ Execution-verified in isolation — the original `iter_lines()` implementation was extracted from the supplied source and replayed with an in-memory chunk provider. The expected-output assertion failed on the original and passed with the proposed remedy. Requests imports, transport behavior, and HTTP integration were not exercised.

## Summary

Fix the CRLF boundary handling before relying on exact line counts or treating blank lines as meaningful records. The inspected test at `tests/test_requests.py:2136` covers ordinary iteration but does not explicitly exercise split CRLF separators.

**Open lead, not scored:** `prepare_url()` uses `if port:` at `models.py:539`, which would omit an integer port of zero during URL reconstruction. Whether an input such as `http://example.com:0/` reaches that branch with `port == 0` depends on the external `urllib3.parse_url()` implementation; that was not established from the supplied workspace.

No files were modified. No external services or runtime integration tests were used; the isolated replay verifies the parser defect and proposed remedy, not end-to-end HTTP behavior.