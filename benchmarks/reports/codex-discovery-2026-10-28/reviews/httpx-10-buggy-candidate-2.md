<!-- run a14fde615d53435cbb2c2af7c940d848; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `httpx/_models.py`, with supporting client, transport, utility, type, documentation, and model-test reads. Completed traces cover query parsing/hashing, header merging, and URL port changes. Response streaming and cookies were not exhaustively reviewed. Eight shell calls; no files changed or runtime tests run.  
**Logic Score:** 72/100

> Four defects are supported by static traces. The score describes confirmed findings within this inspected slice, not overall correctness.

## Findings

### 🟡 Warning — [L3] Blank query values disappear during merging

**Premises:** Empty query values are supported: `tests/models/test_queryparams.py:63–67` expects both `""` and `None` to serialize as `a=`. URL merging must retain unrelated parameters, as demonstrated by `tests/models/test_url.py:151–156`.

**Trace:**

1. `Request("GET", "https://example.org/?a=", params={"b": "1"})` calls `URL.copy_merge_params()` at `_models.py:1094`.
2. `URL.params` constructs `QueryParams("a=")`.
3. At [`_models.py:615`](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L615), `urllib.parse.parse_qs(value)` uses its default `keep_blank_values=False`, producing `{}`.
4. Merging adds only `b=1`; URL serialization cannot recover the discarded `a`.

Rebuttal check: the mapping-input branch preserves empty values, but this string-input path bypasses it.

**Divergence:** **L3** at line 615: a supported empty value is treated as absent. The resulting request URL loses a parameter unrelated to the requested update.

**Trigger:** The request above should produce `https://example.org/?a=&b=1`; the source-derived result is `https://example.org/?b=1`.

**Remedy:** Replace line 615 with:

```python
self._dict = parse_qs(value, keep_blank_values=True)
```

Dry-run: preserves blank values while retaining ordinary nonempty parsing.

**Verification:** Static evidence only. Neither the trigger nor remedy was executed under the requested discovery protocol.

### 🟡 Warning — [L4] Header merging discards repeated input values

**Premises:** Repeated headers are supported: `tests/models/test_headers.py:7–21` requires both values to remain available through `get_list()` and `multi_items()`. `BaseClient.build_request()` accepts `HeaderTypes`, including sequences of pairs, and merges them through `_merge_headers()`.

**Trace:**

1. `build_request(..., headers=[("X-Tag", "one"), ("X-Tag", "two")])` reaches `_client.py:407`, which calls `merged_headers.update(headers)`.
2. [`Headers.update()` at `_models.py:965`](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L965) constructs a `Headers` instance retaining both incoming entries.
3. Its loop assigns `"one"`, then `"two"`, through `Headers.__setitem__()`.
4. The second assignment replaces the first matching entry at line 1013. Only `"two"` remains.

Rebuttal check: preserving duplicates in the constructor does not protect them from the subsequent assignments. Both default transports consume the resulting `request.headers.raw` unchanged.

**Divergence:** **L4** at line 968: sequential replacement destroys an earlier value from the same incoming header collection. Client request construction silently loses supplied header data.

**Trigger:** For the `build_request()` call above, `request.headers.get_list("x-tag")` should retain `["one", "two"]`; the source-derived result is `["two"]`.

**Remedy:** Replace the body of `Headers.update()` with:

```python
headers = Headers(headers)
for key in headers:
    if key in self:
        del self[key]
self._list.extend(headers._list)
```

Dry-run: removes prior values for incoming names once, preserves incoming duplicates, and retains unrelated headers.

**Verification:** Static evidence only. No request was sent, and the replacement was not executed.

### 🟡 Warning — [L6] Equal query objects lack consistent hashes

**Premises:** Order-independent equality is explicitly exercised by `tests/models/test_queryparams.py:40–42`. Hash-based deduplication is supported by `test_queryparams_are_hashable()` at lines 117–125. Equal Python dictionary/set keys must have equal hashes.

**Trace:**

1. Construct `a = QueryParams("a=1&b=2")` and `b = QueryParams("b=2&a=1")`.
2. `QueryParams.__eq__()` sorts both collections of pairs at `_models.py:803`, so `a == b` is `True`.
3. [`QueryParams.__hash__()` at line 797](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L797) hashes `str(self)`, which preserves insertion order: `"a=1&b=2"` versus `"b=2&a=1"`.
4. When those strings have different hashes, dictionary/set lookup does not recognize the objects as equal keys.

Rebuttal check: the existing hashability test uses identical serialized order for equivalent objects, so it does not cover this mismatch.

**Divergence:** **L6**: `__hash__()` fails the behavioral contract required by hash-based consumers. Equal query objects can occupy separate set entries or fail equivalent-key dictionary lookup.

**Trigger:** `{a: "cached"}[b]` should return `"cached"`; it can raise `KeyError` when the two serialized strings hash differently. The particular hash values depend on the interpreter’s hash seed.

**Remedy:** Replace line 798 with:

```python
return hash(tuple(sorted(self.multi_items())))
```

Dry-run: objects equal under the existing comparison now hash the same canonical sequence, including repeated pairs.

**Verification:** Static evidence only. Hash values and lookup results were not measured.

### 🟡 Warning — [L9] Changing an internationalized URL’s port raises an encoding error

**Premises:** Internationalized hosts are supported. `tests/models/test_url.py:10–15,67–73` establishes that the Chinese hostname is stored in IDNA form while `.host` returns Unicode. Port changes are supported independently through `copy_with()`.

**Trace:**

1. Construct `u = URL("http://中国.icom.museum/")`.
2. `u.copy_with(port=8080)` enters the host/port consolidation branch.
3. [`_models.py:464`](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L464) defaults the omitted host to `self.host`, yielding the Unicode string `"中国.icom.museum"`.
4. Line 472 attempts to encode `"中国.icom.museum:8080"` as ASCII, raising `UnicodeEncodeError`.

Rebuttal check: the constructor’s IDNA conversion occurs before this operation; the failing ASCII conversion prevents construction of the updated URL.

**Divergence:** **L9**: host reconstruction uses the decoded display representation where ASCII host bytes are required. A valid port-only update fails.

**Trigger:** `u.copy_with(port=8080)` should return `http://xn--fiqs8s.icom.museum:8080/`; the source-derived consequence is `UnicodeEncodeError`.

**Remedy:** Replace line 464 with:

```python
host = kwargs.pop("host", self.raw_host.decode("ascii")) or ""
```

Dry-run: port-only updates retain IDNA bytes; ASCII hosts remain unchanged, and the existing bracket logic restores IPv6 brackets.

**Verification:** Static evidence only. The trigger and remedy were not executed.

## Summary

Prioritize the query and header data-loss defects, followed by URL port reconstruction and hash consistency. All four findings have concrete source-supported consequences; remedies were checked by mental traces only. Unreviewed response, cookie, and other boundary paths remain coverage omissions, with no additional open lead promoted to a defect.