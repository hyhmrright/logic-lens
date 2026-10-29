<!-- run 3618de795ece4ec1a30143240da80696; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces of `URL.copy_with`, query parsing/equality/hashing, and `Headers.update` in `httpx/_models.py`, supported by model/client tests, client request construction, transport handoff, types, and documentation. Response streaming and Cookies were not deeply reviewed.  
**Logic Score:** 79/100

> Four defects are supported by static evidence. No code or integration tests were executed, and no files were modified.

## Findings

### 🟡 Warning — [L3] Blank query values disappear during parameter merging

Premises: Empty query values are supported: `tests/models/test_queryparams.py:63–67` requires `{"a": ""}` and `{"a": None}` to serialize as `a=`. `tests/models/test_url.py:151–156` requires merging an unrelated parameter to retain existing parameters.

Trace:  
1. `Request("GET", "https://example.org/?a=&b=1", params={"c": "2"})` invokes `URL.copy_merge_params` through `Request.__init__`.  
2. `URL.params` constructs `QueryParams` from the existing query string.  
3. [QueryParams.__init__ at line 615](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L615) calls `urllib.parse.parse_qs(value)` with its default `keep_blank_values=False`, discarding `a=`.  
4. `merge` adds `c=2`; serialization produces `b=1&c=2`.

Rebuttal check: Mapping inputs preserve empty strings, but the existing URL traverses the string-parsing branch. Downstream merging cannot restore the discarded value.

Divergence: **L3** at line 615 silently removes a supported boundary value. The constructed request URL loses a parameter unrelated to the requested change.

Trigger: The request above should contain `?a=&b=1&c=2`; static evaluation produces `?b=1&c=2`. Parsing `"a="` directly also produces an empty `QueryParams`.

Remedy: Replace line 615 with:

```python
self._dict = parse_qs(value, keep_blank_values=True)
```

Dry-run: Blank values survive; ordinary nonempty parameters and repeated values retain their existing behavior.

Verification: **Static evidence only.** The predicted URL was not runtime-observed; the remedy was checked by reasoning only.

### 🟡 Warning — [L6] Header merging discards repeated incoming values

Premises: `HeaderTypes` accepts sequences of pairs (`httpx/_types.py:46–52`). `tests/models/test_headers.py:7–21` establishes that repeated names retain all values. Client request construction promises to merge supplied headers (`httpx/_client.py:329–340`).

Trace:  
1. `Client.build_request` passes supplied headers through `_merge_headers`, which calls `Headers.update`.  
2. [Headers.update at line 965](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L965) iterates each incoming raw pair and assigns it with `self[key] = value`.  
3. `Headers.__setitem__`, at lines 993–1015, replaces existing entries for that name. Thus the second `Accept` value overwrites the first.  
4. The transport receives the already-reduced `request.headers.raw` (`httpx/_transports/default.py:213`).

Rebuttal check: Constructing `Headers` directly preserves duplicates, but client merging necessarily traverses `update`. The transport does not recover lost values.

Divergence: **L6:** `update` uses a replacement operation as though it preserved successive values. The resulting request advertises only the final supplied value.

Trigger:

```python
request = client.build_request(
    "GET", "https://example.org/",
    headers=[("Accept", "application/json"), ("Accept", "text/plain")],
)
```

Expected: Both media types remain represented. Actual static result: `request.headers.get_list("accept") == ["text/plain"]`.

Remedy: Replace the `update` body with:

```python
headers = Headers(headers)
for key in headers.keys():
    if key in self:
        del self[key]
self._list.extend(headers._list)
```

Dry-run: Incoming duplicates survive, existing values for supplied names are replaced, and unrelated headers remain.

Verification: **Static evidence only.** Neither request construction nor the proposed remedy was executed.

### 🟡 Warning — [L9] Changing a port crashes for internationalized hosts

Premises: Internationalized hosts are supported by `tests/models/test_url.py:6–73`; `.host` returns Unicode while `.raw_host` returns IDNA bytes. Port replacement is supported by the same file’s lines 89–91.

Trace:  
1. Constructing `URL("https://中国.icom.museum/")` provides `.host == "中国.icom.museum"`.  
2. Calling `.copy_with(port=8443)` enters the host/port consolidation branch.  
3. [Line 464](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L464) selects the Unicode `.host` as the unchanged hostname.  
4. Line 472 evaluates `"中国.icom.museum:8443".encode("ascii")`, raising `UnicodeEncodeError`.

Rebuttal check: The final `URL(...)` constructor supports IDNA conversion, but this exception occurs before that constructor is reached.

Divergence: **L9** at lines 472–474 attempts ASCII encoding before IDNA conversion. A valid URL cannot undergo a supported port change.

Trigger:

```python
httpx.URL("https://中国.icom.museum/").copy_with(port=8443)
```

Expected: `https://xn--fiqs8s.icom.museum:8443/`. Actual static consequence: `UnicodeEncodeError`. Explicitly supplying a Unicode `host` reaches the same failure.

Remedy: Immediately after line 464, insert:

```python
if any(ord(char) > 127 for char in host):
    host = idna.encode(host, uts46=True).decode("ascii")
```

Dry-run: The supplied Unicode hostname becomes IDNA ASCII before port assembly; existing ASCII and IPv6 handling remain on their current paths.

Verification: **Static evidence only.** The exception and remedy were not executed.

### 🟡 Warning — [L6] Equal query parameters can fail dictionary lookup

Premises: Equality explicitly ignores parameter order (`tests/models/test_queryparams.py:40–42`). Hashability and set deduplication are supported at lines 117–125. Python requires equal hashable objects to have equal hashes.

Trace:  
1. Construct `p = QueryParams("a=1&b=2")` and `q = QueryParams("b=2&a=1")`.  
2. [__eq__ at line 803](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L803) sorts their pairs, yielding `p == q`.  
3. `__hash__` at line 798 instead hashes `str(self)`. Serialization preserves insertion order, producing two different strings.  
4. When those strings have different hashes, dictionary lookup using `q` cannot match an entry stored under `p`.

Rebuttal check: Immutability prevents later mutation, but does not reconcile these two representations. Existing hashability tests exercise only single-key inputs.

Divergence: **L6:** The hash implementation violates the equality contract consumed by dictionaries and sets. Equal parameter objects can occupy separate set entries or miss existing dictionary entries.

Trigger: With the two objects above, in a process where their string hashes differ, `{p: "hit"}[q]` raises `KeyError` instead of returning `"hit"`; `len({p, q})` is two instead of one.

Remedy: Replace line 798 with:

```python
return hash(tuple(sorted(self.multi_items())))
```

Dry-run: Every pair considered equal now has the same canonical hash input, including reordered repeated values.

Verification: **Static evidence only.** No process-specific hash values or collection results were measured.

## Summary

The confirmed consequences are lost query parameters, lost header values, an exception during valid URL editing, and unreliable hash-based lookup. Proposed remedies were reviewed statically only.

The score covers this inspected slice, with one deduction per unique L-code in `_models.py`; it does not establish whole-file correctness. No additional open lead is asserted as a defect.