<!-- run a0f6345905054ca0a713aea52b626b39; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Focused review of `httpx/_models.py`: `QueryParams.__init__`, `QueryParams.__hash__`, and `Headers.update`, including supporting methods, client call paths, and tests. Other behavior is not exhaustively reviewed.  
**Logic Score:** 86/100

> Three source-confirmed defects were found. Consequences below are established by static execution traces, not runtime observations.

## Findings

### 🟡 Warning
**[L3] — Parsing silently drops empty query values**

Premises: String and mapping inputs are both supported query representations. Empty values are explicitly supported: [test_queryparams.py:63](tests/models/test_queryparams.py#L63) expects `{"a": ""}` to serialize as `a=`.

Trace: [1] [`QueryParams.__init__`, line 615](httpx/_models.py#L615) passes string input to the imported `urllib.parse.parse_qs` without `keep_blank_values=True`. [2] Its default behavior discards empty-valued fields, so `"a=&b=2"` becomes `{"b": ["2"]}`. [3] `multi_items()` and `__str__()` serialize only those surviving fields. [4] This also affects existing URL parameters: `Request.__init__` → `copy_merge_params` → `URL.params` reparses the original query before merging. Rebuttal check: PASSED — mapping inputs preserve empty values, and the inspected call paths contain no restoration or rejection.

Divergence: **L3:** A valid empty parameter disappears. For example, adding `b=2` to a request URL containing `a=` produces a URL with only `b=2`, changing the query supplied to the server.

Trigger:
```python
q = httpx.QueryParams("a=&b=2")
# Expected: q.get_list("a") == [""]
# Actual by trace: []

r = httpx.Request("GET", "https://example.org/?a=", params={"b": "2"})
# Expected query: a=&b=2
# Actual by trace: b=2
```

Remedy: At line 615, replace the assignment with:
```python
self._dict = parse_qs(value, keep_blank_values=True)
```
Dry-run: ✅ Empty values survive parsing and merging; ordinary nonempty values retain their behavior.

Verification: ⚠️ Unverified at runtime — source trace only under the discovery protocol.

### 🟡 Warning
**[L6] — Equal query objects can have different hashes**

Premises: `QueryParams` is intentionally hashable; [test_queryparams.py:117](tests/models/test_queryparams.py#L117) uses instances in a set. Equality explicitly ignores ordering, including the reversed-key example at line 40. Python requires equal hashable objects to have equal hashes.

Trace: [1] [`__eq__`, line 803](httpx/_models.py#L803) sorts both objects’ key/value pairs, making `"a=1&b=2"` equal to `"b=2&a=1"`. [2] `multi_items()` retains each object’s insertion order. [3] [`__hash__`, line 798](httpx/_models.py#L798) hashes `str(self)`, so those equal objects hash different strings. Rebuttal check: PASSED — neither construction nor hashing canonicalizes ordering; existing hash tests cover identical ordering only.

Divergence: **L6:** The equality/hash contracts disagree. Whenever the two string hashes differ, dictionary lookup by the equal object misses, and sets retain both objects. An accidental hash collision can mask a particular example.

Trigger:
```python
a = httpx.QueryParams("a=1&b=2")
b = httpx.QueryParams("b=2&a=1")
assert a == b
# Expected: {a: "value"}[b] == "value"; len({a, b}) == 1
# Actual when hashes differ: KeyError; set length 2
```

Remedy: Replace the body of `QueryParams.__hash__` with:
```python
return hash(tuple(sorted(self.multi_items())))
```
Dry-run: ✅ Equal objects now hash identical canonical tuples; duplicate pairs remain represented, and serialization order is unchanged.

Verification: ⚠️ Unverified at runtime — no process-specific hash results were measured.

### 🟡 Warning
**[L6] — Header updates discard repeated incoming values**

Premises: `Headers` supports repeated fields, as established by [test_headers.py:6](tests/models/test_headers.py#L6). Header arguments accept sequences of pairs. Client header construction and request merging both call `Headers.update()`.

Trace: [1] [`Headers.update`, line 966](httpx/_models.py#L966) constructs a temporary `Headers` that preserves all incoming pairs. [2] Line 968 assigns each pair through `__setitem__`. [3] [`__setitem__`, lines 1008–1013](httpx/_models.py#L1008) removes duplicates and replaces the existing value. Thus the second incoming occurrence replaces the first. [4] [`Client._merge_headers`, line 407](httpx/_client.py#L407) uses this operation before constructing the request. Rebuttal check: PASSED — replacement is appropriate for individual assignment, but applying it repeatedly loses values from the incoming multidict; the client path provides no recovery.

Divergence: **L6:** Updating with two values retains only the last. A request built through `Client.build_request()` consequently loses earlier repeated header values, while constructing `Headers` directly preserves them.

Trigger:
```python
h = httpx.Headers()
h.update([("X-Tag", "one"), ("X-Tag", "two")])
# Expected: h.get_list("X-Tag") == ["one", "two"]
# Actual by trace: ["two"]
```

Remedy: Keep line 966, then replace the update loop with the following. The first occurrence replaces old destination values; subsequent occurrences append using the existing destination encoding behavior:
```python
seen = set()
for key, value in headers.raw:
    name = key.decode(headers.encoding)
    text = value.decode(headers.encoding)
    normalized = name.lower()
    if normalized not in seen:
        self[name] = text
        seen.add(normalized)
    else:
        encoding = self._encoding or "utf-8"
        raw_name = name.encode(encoding)
        self._list.append(
            (raw_name, raw_name.lower(), text.encode(encoding))
        )
```
Dry-run: ✅ Both incoming values survive, prior values for that name are replaced, and single-value updates retain their behavior.

Verification: ⚠️ Unverified at runtime — replacement was traced mentally, not executed.

## Summary

Prioritize preserving empty query values and repeated headers because both affect constructed requests. The score deducts seven points for L3 and seven for L6, applying the supplied per-code deduction cap.

**Open leads:** Cached response text after changing encoding, and invalid chunk sizes, were inspected preliminarily but not fully adjudicated; neither is counted as a defect. The suspected general stream-cleanup issue was excluded because client stream contexts provide `finally` cleanup and manual streaming documents caller ownership.

Six shell calls were used. No files were modified, no external services or history were accessed, and no runtime or integration tests were run.