<!-- run 2e5e6d77fb6d4e0a9070d41a7e5d17d6; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted review of `httpx/_models.py`: `QueryParams.__init__`, `QueryParams.__hash__`, and `Headers.update`, including their local collaborators, URL/request construction, and relevant tests. Other behavior was not exhaustively reviewed.
**Logic Score:** 71/100

> Three concrete defects were reproduced with isolated, in-memory probes.

## Findings

### 🔴 Critical
**[L3] — Parsing query strings silently discards empty-valued parameters**

Premises: `QueryParams` accepts both strings and mappings. Empty values are supported: `tests/models/test_queryparams.py:63–67` explicitly checks that mapping values `""` and `None` serialize as `a=`.

Trace: [1] `QueryParams("a=&b=2")` enters the string branch at `_models.py:613`. [2] Line 615 calls the imported `urllib.parse.parse_qs` without `keep_blank_values=True`, producing only `{"b": ["2"]}`. [3] Serialization at line 806 consequently returns `b=2`. The same parser backs `URL.params` at line 348, which feeds URL parameter modification. Rebuttal check: PASSED — strings are explicitly supported; no guard rejects empty values; subsequent serialization cannot restore discarded data.

Divergence: **L3**, at [httpx/_models.py:615](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L615). Expected `[("a", ""), ("b", "2")]`; observed `[("b", "2")]`. This loses the distinction between an absent parameter and a present parameter with an empty value. Reconstructing or modifying a URL through these parameters can remove existing empty-valued fields.

Trigger: `httpx.QueryParams("a=&b=2").multi_items()` returns `[("b", "2")]`.

Remedy: Replace line 615 with:
```python
self._dict = parse_qs(value, keep_blank_values=True)
```
Dry-run: ✅ Empty values survive; empty input and repeated nonempty values retain their behavior.

Verification: ✅ Execution-verified — the original extracted class failed the expected-items assertion; the in-memory remedy passed.

### 🟡 Warning
**[L6] — Equal query parameters can fail dictionary lookup and set deduplication**

Premises: `QueryParams` is hashable. Equality explicitly ignores ordering, and `tests/models/test_queryparams.py:40–42` confirms that differently ordered mappings compare equal. Python hash collections require equal keys to have equal hashes.

Trace: [1] Construct `a = QueryParams("a=1&b=2")` and `b = QueryParams("b=2&a=1")`. [2] `_models.py:803` sorts both item collections, yielding `a == b`. [3] Line 798 instead hashes their differently ordered serialized strings. [4] The probe observed unequal hashes, two set entries, and a failed lookup using the equal key. Rebuttal check: PASSED — ordering independence is deliberate; neither construction nor hash collection use enforces canonical ordering.

Divergence: **L6**, at [httpx/_models.py:798](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L798). Expected interchangeable dictionary keys and one set entry; observed `{a: "value"}.get(b) is None` and `len({a, b}) == 2`. This breaks caching and deduplication when equivalent parameters arrive in different orders.

Trigger:
```python
a = httpx.QueryParams("a=1&b=2")
b = httpx.QueryParams("b=2&a=1")
assert a == b
assert {a: "value"}[b] == "value"  # Observed lookup failure
```

Remedy: Replace line 798 with:
```python
return hash(tuple(sorted(self.multi_items())))
```
Dry-run: ✅ Hashing now uses the same canonical items as equality, including duplicate values; serialization order remains unchanged.

Verification: ✅ Execution-verified — original: unequal hashes, set size 2, lookup miss. In-memory remedy: equal hashes, set size 1, successful lookup.

### 🟡 Warning
**[L9] — Updating headers retains an incompatible inferred encoding**

Premises: `Headers` accepts raw byte pairs and automatically detects ASCII, UTF-8, or ISO-8859-1. The tests at `tests/models/test_headers.py:116–143` establish this fallback behavior. The detected encoding is cached.

Trace: [1] Create `Headers({"x": "old"})`. [2] `update([(b"x", b"\xc3\xa9")])` checks membership at `_models.py:968`; this detects and caches ASCII from the old headers. [3] Line 970 inserts the UTF-8 bytes without invalidating that cache. [4] Reading `h["x"]` at line 985 decodes those bytes as ASCII and raises `UnicodeDecodeError`. Rebuttal check: PASSED — byte input and UTF-8 detection are supported; no explicit encoding was chosen; `update` completes without rejecting or correcting the incompatible state.

Divergence: **L9**, at [httpx/_models.py:970](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L970). Expected `h["x"] == "é"` after updating with valid UTF-8 bytes; observed `UnicodeDecodeError`. Constructing fresh headers from the same final raw bytes correctly detects UTF-8.

Trigger:
```python
h = httpx.Headers({"x": "old"})
h.update([(b"x", b"\xc3\xa9")])
h["x"]  # UnicodeDecodeError
```

Remedy: Preserve explicit encoding choices separately and invalidate inferred encoding after updates:

- After `self._encoding = encoding` in `Headers.__init__`, add `self._explicit_encoding = encoding`.
- After `self._encoding = value` in the encoding setter, add `self._explicit_encoding = value`.
- After `self._list.extend(headers._list)` in `update`, add `self._encoding = self._explicit_encoding`.

Dry-run: ✅ The trigger redetects UTF-8; constructor-specified and setter-specified encodings remain respected.

Verification: ✅ Execution-verified — original raised `UnicodeDecodeError`; the in-memory remedy returned `"é"`. Explicit-encoding checks also passed.

## Summary

The defects cause parameter loss, broken hash collection behavior, and header decoding failures. No open lead was promoted to a finding.

Verification used workspace-extracted classes and helpers with standard-library dependencies; remedies existed only in memory. No files were modified, no external services were accessed, and no runtime integration tests or full package suite were run. Transport behavior and complete package integration remain unverified.