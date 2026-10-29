<!-- run ead2e9daad6540629fbf86bbb463659a; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Three paths in `httpx/_models.py`: URL component copying and its host accessor; query-parameter construction and round trips; query equality/hash behavior. Supporting tests and callers inspected. This is a partial-file review.
**Logic Score:** 86/100

> Four source-supported defects found. Consequences below follow from static traces; they were not observed through runtime execution.

## Findings

### 🟡 Warning
**[L6] — Parsing query strings silently discards empty values**

Premises: String and mapping inputs are supported representations of `QueryParams`. `tests/models/test_queryparams.py:63–67` explicitly preserves mapping values `""` and `None` as `a=`. The imported `urllib.parse.parse_qs` discards blank values unless `keep_blank_values=True`.

Trace: [1] [`_models.py:613–615`](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L613) routes `"a=&b=2"` to `parse_qs(value)` without that option, producing only `{"b": ["2"]}`. [2] `multi_items()` at line 689 traverses this reduced dictionary. [3] `__str__()` at line 806 serializes it as `"b=2"`. `URL.params` also uses this constructor at line 348, so adding another parameter can remove existing empty-valued parameters. Rebuttal check: PASSED — string inputs are accepted directly; no guard or later reconstruction restores the discarded values.

Divergence: **L6:** expected empty-valued parameters to survive parsing and modification; actual behavior loses them. Even `QueryParams(str(QueryParams({"a": ""})))` loses `a`.

Trigger: `str(httpx.URL("https://example.org/?a=").copy_add_param("b", "2"))`  
Expected: `"https://example.org/?a=&b=2"`  
Source-derived actual: `"https://example.org/?b=2"`.

Remedy: At line 615, replace the assignment with:
```python
self._dict = parse_qs(value, keep_blank_values=True)
```
Dry-run: ✅ `a` retains `[""]`, adding `b` preserves it, and serialization emits `a=&b=2`; ordinary nonempty values and empty input retain their behavior.

Verification: ⚠️ Unverified — static trace only; no runtime tests performed.

### 🟡 Warning
**[L9] — Changing an internationalized URL’s port raises an encoding exception**

Premises: `URL.host` deliberately returns decoded Unicode, while `URL.raw_host` returns ASCII IDNA bytes. These contracts are asserted in `tests/models/test_url.py:67–73`. `copy_with(port=...)` accepts an integer without requiring a replacement host.

Trace: [1] For `URL("https://xn--bcher-kva.de/")`, `host` decodes to `"bücher.de"` at lines 246–247. [2] [`copy_with`, line 464](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L464) uses this Unicode property as the default host when changing the port. [3] Line 472 calls `"bücher.de:8443".encode("ascii")`, raising `UnicodeEncodeError` before the final URL constructor can encode the hostname. Explicit Unicode `host=` values encounter the same problem. Rebuttal check: PASSED — the hostname is already supported by URL construction, the port branch is directly reachable, and no exception handler or IDNA conversion protects this encoding.

Divergence: **L9:** expected a copied URL with the original hostname and new port; actual behavior raises an exception for a valid hostname.

Trigger: `httpx.URL("https://xn--bcher-kva.de/").copy_with(port=8443)`  
Expected: `"https://xn--bcher-kva.de:8443/"`  
Source-derived actual: `UnicodeEncodeError`.

Remedy: Replace line 464 with the following, leaving the subsequent port and IPv6 handling in place:
```python
host = kwargs.pop("host", self.raw_host.decode("ascii")) or ""
if any(ord(char) > 127 for char in host):
    host = URL(f"//{host}").raw_host.decode("ascii")
```
This reuses existing URL parsing for explicit Unicode hosts. Dry-run: ✅ the default host remains ASCII IDNA, explicit Unicode hosts are encoded before authority construction, and ASCII/IPv6 paths retain their existing handling.

Verification: ⚠️ Unverified — static trace only; proposed replacement was not executed.

### 🟡 Warning
**[L9] — Unicode host decoding misses internationalized labels after an ASCII prefix**

Premises: The `host` property promises Unicode representation of internationalized domain names. Its stored hostname can contain multiple labels, including ordinary ASCII labels followed by IDNA labels.

Trace: [1] For `URL("https://www.xn--bcher-kva.de/")`, the stored host is `"www.xn--bcher-kva.de"` at line 240. [2] [`_models.py:246`](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L246) evaluates `host.startswith("xn--")` as false because the first label is `www`. [3] Line 249 returns the unchanged ASCII hostname without invoking `idna.decode`. Rebuttal check: PASSED — this is a valid hostname, the accessor is public, and no subsequent decoding occurs before return. Existing IDNA test cases place the encoded label first.

Divergence: **L9:** expected `.host == "www.bücher.de"`; actual return value is `"www.xn--bcher-kva.de"`. This violates the public accessor contract; it does not establish a transport-routing failure.

Trigger: `httpx.URL("https://www.xn--bcher-kva.de/").host`.

Remedy: Replace line 246 with:
```python
if any(label.startswith("xn--") for label in host.split(".")):
```
Keep the existing `idna.decode(host)` body. Dry-run: ✅ the second label triggers decoding, first-label IDNA names still decode, and ASCII-only/IPv6 hosts retain their current paths.

Verification: ⚠️ Unverified — static trace only; no runtime tests performed.

### 🟡 Warning
**[L6] — Equal query objects can have different hashes**

Premises: `QueryParams.__eq__` compares sorted parameter pairs, making equality independent of their order. Tests at `tests/models/test_queryparams.py:40–42` affirm this behavior, and lines 117–125 establish use in sets. Equal hashable objects must have equal hashes.

Trace: [1] Constructing `"a=1&b=2"` and `"b=2&a=1"` retains their respective key orders. [2] [`_models.py:803`](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L803) sorts their pairs and returns equality. [3] Line 798 instead hashes each object’s order-preserving string representation, yielding independently computed hashes for different strings. Rebuttal check: PASSED — both inputs are supported, public hashing is enabled, and no canonicalization reconciles hashing with equality. The existing hashability test covers only single-key objects.

Divergence: **L6:** expected interchangeable dictionary keys and set deduplication; actual behavior can produce failed lookups and duplicate equal set members. Accidental string-hash collisions can mask the symptom.

Trigger:
```python
a = httpx.QueryParams("a=1&b=2")
b = httpx.QueryParams("b=2&a=1")
assert a == b
assert {a: "found"}[b] == "found"
```
Expected: successful lookup. Source-derived actual: `KeyError` when the hashes differ.

Remedy: Replace the return expression in `QueryParams.__hash__` at line 798 with:
```python
return hash(tuple(sorted(self.multi_items())))
```
Dry-run: ✅ both objects produce identical hash inputs; duplicate parameter multiplicity is preserved, and serialization remains unchanged.

Verification: ⚠️ Unverified — static trace only; no runtime tests performed.

## Summary

Prioritize preserving blank query values and repairing URL host encoding, then align hashing with equality and complete host decoding. The framework’s per-L-code deduction cap yields 86/100 across two affected categories.

**Open leads:** None retained as findings. Headers, cookies, and response streaming remain outside the traced subset. No files were modified, and no external services, history, or runtime integration tests were used.