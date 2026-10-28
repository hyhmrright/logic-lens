<!-- run 6fb8450f9e3e4fa8b5b6496718aba491; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted review of `httpx/_models.py`: `QueryParams.__init__`, `QueryParams.__hash__` and equality helpers, and `URL.copy_with`; supporting URL properties, request construction, and local tests. Other functionality was not exhaustively reviewed.  
**Logic Score:** 79/100

> Three concrete defects follow from static execution traces. No runtime results are claimed.

## Findings

### 🟡 Warning
**[L3] — Parsing silently drops query parameters with empty values**

Premises: String and mapping inputs both construct `QueryParams`. Empty values are supported: [test_queryparams.py:63](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L63) explicitly expects `{"a": ""}` to serialize as `a=`.

Trace: [1] At [_models.py:615](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L615), `"a=&b=1"` enters `urllib.parse.parse_qs` without `keep_blank_values=True`; its default behavior discards `a`. [2] `multi_items()` therefore contains only `("b", "1")`. [3] `__str__()` serializes that reduced collection as `b=1`. Request construction also reaches this parsing through `copy_merge_params` when a `params` argument is supplied. Rebuttal check: PASSED — premise: local tests establish empty-value support; path: public string input has no rejecting guard; consequence: merging and serialization cannot restore the discarded value.

Divergence: **L3:** The blank-value boundary silently changes parameter presence. Expected `"a=&b=1"`; derived actual `"b=1"`. Likewise, adding a parameter to an existing URL can delete its unrelated empty-valued parameters.

Trigger:
```python
q = httpx.QueryParams("a=&b=1")
assert q.get_list("a") == [""]       # Actual: []
assert str(q) == "a=&b=1"            # Actual: "b=1"
```

Remedy: Replace line 615 with:
```python
self._dict = parse_qs(value, keep_blank_values=True)
```
Dry-run: ✅ Parsing retains `a: [""]`, serialization emits `a=&b=1`, and nonempty values remain unchanged.

Verification: ⚠️ Static trace only; not execution-verified under the requested discovery protocol.

### 🟡 Warning
**[L6] — Equal query parameters can behave as different dictionary keys**

Premises: `QueryParams` is deliberately hashable. Its equality ignores pair ordering: [test_queryparams.py:40](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L40) explicitly equates mappings with opposite insertion orders. Python requires equal objects to have equal hashes.

Trace: [1] Constructing `a` from `"a=1&b=2"` and `b` from `"b=2&a=1"` preserves their different key insertion orders. [2] At [_models.py:803](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L803), equality sorts both pair lists, so `a == b` is true. [3] At line 798, hashing instead hashes their differently ordered serialized strings. [4] Unless those strings happen to collide, dictionary lookup using `b` cannot find an entry stored using `a`. Rebuttal check: PASSED — premise: order-independent equality is tested; path: both constructors and hashing are public; consequence: no canonicalization reconciles hashing with equality. The existing hashability test covers single-key inputs only.

Divergence: **L6:** The hash implementation violates the contract required by dictionary/set callers. Equal objects can occupy separate set entries or fail dictionary lookup.

Trigger:
```python
a = httpx.QueryParams("a=1&b=2")
b = httpx.QueryParams("b=2&a=1")
assert a == b
assert {a: "found"}[b] == "found"   # Can raise KeyError
```
A coincidental string-hash collision can mask this particular trigger; it does not repair the contract.

Remedy: Replace `QueryParams.__hash__`’s return expression at line 798 with:
```python
return hash(tuple(sorted(self.multi_items())))
```
Dry-run: ✅ Both objects produce the same sorted tuple and hash. Duplicate-pair multiplicity is retained, and serialization order remains unchanged.

Verification: ⚠️ Static trace only; no process-specific hashes or dictionary results were measured.

### 🟡 Warning
**[L9] — Changing an internationalized URL’s port raises `UnicodeEncodeError`**

Premises: `URL.host` intentionally returns decoded Unicode, while `raw_host` returns IDNA bytes. [test_url.py:10](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_url.py#L10) establishes this behavior for `中国.icom.museum`. `copy_with(port=...)` accepts an integer and preserves the existing host.

Trace: [1] At [_models.py:464](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L464), a port-only update defaults `host` to `self.host`, yielding the Unicode string `"中国.icom.museum"`. [2] Port `8443` is retained and the IPv6 branch is skipped. [3] Line 472 evaluates `"中国.icom.museum:8443".encode("ascii")`, raising `UnicodeEncodeError`. [4] Execution never reaches the final `URL(...)` construction that could perform IDNA conversion. Rebuttal check: PASSED — premise: Unicode hosts are explicitly supported; path: the accepted port-only update reaches this branch directly; consequence: there is no surrounding conversion or exception fallback.

Divergence: **L9:** Expected `https://xn--fiqs8s.icom.museum:8443/`; derived actual behavior is an encoding exception. Explicitly supplying a Unicode `host` reaches the same failure.

Trigger:
```python
httpx.URL("https://中国.icom.museum/").copy_with(port=8443)
```

Remedy: Insert immediately after the `host` assignment at line 464:
```python
if any(ord(char) > 127 for char in host):
    host = idna.encode(host, uts46=True).decode("ascii")
```
Dry-run: ✅ The host becomes ASCII IDNA before authority encoding; the requested port survives. Existing ASCII and IPv6 hosts bypass the new conversion.

Verification: ⚠️ Static trace only; IDNA conversion and the proposed remedy were not executed.

## Summary

The strongest consequences are silent parameter loss, unreliable dictionary/set behavior, and exceptions during supported URL updates. These warrant fixes before relying on those behaviors; the score covers only the selected scope.

**Open lead, not scored:** `URL.copy_with` quotes usernames and passwords with `quote()`’s default slash handling at lines 457–458. Slash-containing credentials merit investigation, but their final parser-level consequence was not established here.

Investigation used six shell calls. No files were modified, no external services or history were accessed, and no runtime tests were run. Remedies received mental dry-runs only.