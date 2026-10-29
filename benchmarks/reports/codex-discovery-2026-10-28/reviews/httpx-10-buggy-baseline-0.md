<!-- run b47fdb7d3e2748b5a4d6c3c483c1a38d; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Partial review of `httpx/_models.py`: deep traces of `QueryParams.__init__`, query-parameter hashing/equality, and `Headers.update`, with supporting URL, client, and test code. Other behavior was sampled, not exhaustively reviewed.  
**Logic Score:** 86/100

> Three concrete defects were identified by static tracing. No files were modified, external services accessed, or runtime tests executed. “Observed” below means behavior derived from source, not execution.

## Findings

### 🟡 Warning
**[L3] — Parsing silently discards blank query values**

Premises: Query parameters support empty values: `tests/models/test_queryparams.py:60–67` expects dictionary values `""` and `None` to serialize as `a=`. String and dictionary inputs represent the same parameter model.

Trace: [1] At `httpx/_models.py:613–615`, string input reaches imported `urllib.parse.parse_qs` without `keep_blank_values=True`. [2] Its default behavior drops blank values, so `"a=&b=2"` becomes `{"b": ["2"]}`. [3] `URL.params` at line 348 uses this constructor; `copy_set_param` at line 540 parses existing parameters before rebuilding the query. Consequently, adding another parameter also removes existing blank ones. Rebuttal check: PASSED — public inputs accept these strings, tests explicitly support empty values, and rebuilding cannot restore discarded data.

Divergence: **L3:** At line 615, expected `a=` to remain present with value `""`; observed it disappears. For example, changing an unrelated parameter can remove an existing empty-valued query field and alter the outgoing request.

Trigger:
```python
q = httpx.QueryParams("a=&b=2")
assert q.get_list("a") == [""]  # Observed: []

u = httpx.URL("https://example.org/?a=&b=2").copy_set_param("c", "3")
# Expected query: a=&b=2&c=3
# Observed query: b=2&c=3
```

Remedy: At `httpx/_models.py:615`, replace the assignment with:
```python
self._dict = parse_qs(value, keep_blank_values=True)
```
Dry-run: ✅ Blank fields survive parsing and URL reconstruction; nonempty fields retain their behavior.

Verification: ⚠️ Unverified by execution — static trace only under the requested discovery protocol.

### 🟡 Warning
**[L6] — Equal query-parameter objects can have different hashes**

Premises: Python requires equal hashable objects to have equal hashes. The workspace explicitly supports order-independent equality in `tests/models/test_queryparams.py:40–42`, and set membership in `test_queryparams_are_hashable`.

Trace: [1] `QueryParams("a=1&b=2")` and `QueryParams("b=2&a=1")` preserve different insertion orders. [2] At `httpx/_models.py:803`, `__eq__` sorts their items and returns `True`. [3] At lines 798 and 806, `__hash__` hashes their differently ordered serializations instead. Rebuttal check: PASSED — both construction orders are accepted, equality deliberately ignores that order, and no canonicalization occurs before hashing.

Divergence: **L6:** `__hash__` violates the equality/hash protocol. Expected equal objects to act as one dictionary key or set member; observed the implementation permits separate entries and failed lookups through an equal object whenever the string hashes differ. Accidental hash collisions can mask a particular example.

Trigger:
```python
a = httpx.QueryParams("a=1&b=2")
b = httpx.QueryParams("b=2&a=1")
assert a == b
assert hash(a) == hash(b)  # Generally fails.
assert len({a, b}) == 1   # Can produce 2.
```

Remedy: Replace the return expression at `httpx/_models.py:798` with:
```python
return hash(tuple(sorted(self.multi_items())))
```
Dry-run: ✅ Equal sorted item sequences now produce identical hashes, including reordered repeated values; serialization remains unchanged.

Verification: ⚠️ Unverified by execution — static trace only; exact hash values depend on the Python process.

### 🟡 Warning
**[L6] — Updating headers loses repeated incoming fields**

Premises: `Headers` supports repeated names, demonstrated by `tests/models/test_headers.py:6–20`. Client request construction calls `Headers.update` through `_merge_headers` at `httpx/_client.py:399–408`, so this affects ordinary request construction.

Trace: [1] At `httpx/_models.py:966`, constructing `Headers` preserves both incoming `X-Tag` entries. [2] The first iteration at lines 967–968 assigns `"one"` through `Headers.__setitem__`. [3] The second assignment finds the same normalized key and replaces its existing entry at line 1013 with `"two"`. Rebuttal check: PASSED — repeated fields are accepted, client merging reaches this path, and later request construction copies only the surviving field. Existing tests establish that request values override client defaults; they do not justify discarding repetitions within the incoming request values.

Divergence: **L6:** `update` uses a setter whose contract removes duplicates. Expected both incoming values to survive while replacing previous values for that name; observed only the final value survives. Requests built through a client therefore lose earlier repeated header values.

Trigger:
```python
h = httpx.Headers()
h.update([("X-Tag", "one"), ("X-Tag", "two")])
assert h.get_list("X-Tag") == ["one", "two"]
# Observed: ["two"]
```

Remedy: Replace the body of `Headers.update` with:
```python
headers = Headers(headers)
incoming_keys = {key for _, key, _ in headers._list}
self._list = [
    item for item in self._list if item[1] not in incoming_keys
]
self._list.extend(headers._list)
```
Dry-run: ✅ Incoming repetitions survive, previous values for matching names are removed, and unrelated headers remain. Updated names move to the end of the header list.

Verification: ⚠️ Unverified by execution — static trace only; outgoing requests were not exercised.

## Summary

Prioritize preserving blank query values and repeated headers because both can change request contents. The score deducts once for L3 and once for L6, following the supplied per-code deduction cap.

**Open leads:** Response streaming cleanup received preliminary inspection only; no general leak is asserted. In particular, `Client.send` closes the response after read exceptions at `_client.py:901–903`. Cookie semantics, remaining URL behavior, and cancellation paths need further review before drawing conclusions.