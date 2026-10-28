<!-- run 776bc6c26637413288bbf592a129dc7e; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** [httpx/_models.py](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py), prioritizing query parsing, equality/hashing, URL copying, and response text caching. Supporting evidence includes client callers, decoders, tests, and documentation. Headers, cookies, and streaming lifecycle paths were not exhaustively traced.  
**Logic Score:** 72/100

Four defects are supported by static traces. The score describes confirmed findings in the inspected slice, not whole-project correctness. Nine read-only tool calls were used; no files were modified or runtime tests executed.

## Findings

### 🟡 Warning — [L3] Empty query values disappear when parameters are parsed or merged

Premises: Empty values are supported: `tests/models/test_queryparams.py:63–67` requires `{"a": ""}` and `{"a": None}` to serialize as `a=`. String inputs are supported too. The merge contract preserves existing keys while adding others (`tests/models/test_url.py:151–156`).

Trace:

1. `Request.__init__`, lines 1094–1096, passes supplied parameters to `URL.copy_merge_params()`.
2. That method, lines 548–549, obtains existing parameters through `URL.params`.
3. `URL.params`, line 348, constructs `QueryParams` from the existing query string.
4. `QueryParams.__init__`, line 615, calls the imported `urllib.parse.parse_qs(value)` with its default `keep_blank_values=False`. Thus `flag=&x=1` becomes only `{"x": ["1"]}`.
5. `merge()` and `copy_with()` serialize the reduced mapping. No subsequent step restores `flag`.

Divergence: **L3**, line 615: parsing treats a present empty parameter as absent. Adding an unrelated parameter can therefore change the request’s existing meaning.

Trigger:

```python
r = httpx.Request(
    "GET", "https://example.org/?flag=&x=1", params={"y": "2"}
)
```

Expected query: `flag=&x=1&y=2`. Derived actual query: `x=1&y=2`.

Remedy: Replace line 615 with:

```python
self._dict = parse_qs(value, keep_blank_values=True)
```

Dry-run: preserves empty entries while retaining ordinary and repeated values; mentally checked only.

Verification: **Static evidence only.** No execution was attempted under the discovery protocol.

### 🟡 Warning — [L9] Copying a Unicode hostname attempts ASCII encoding before IDNA encoding

Premises: Unicode hostnames are supported, and `.host` returns decoded Unicode (`tests/models/test_url.py:6–73`). `URL.copy_with()` explicitly accepts component replacements, including ports and hosts.

Trace:

1. Constructing `URL("https://中国.icom.museum/")` produces a URL whose `.host` is `"中国.icom.museum"`, as established by the IDNA tests.
2. Calling `.copy_with(port=8443)` enters the host/port branch at line 462.
3. Line 464 obtains the unchanged hostname from `self.host`, yielding Unicode.
4. Line 472 executes `f"{host}:{port}".encode("ascii")`, raising `UnicodeEncodeError`.
5. The final `URL(...)` construction at line 537—which could perform IDNA conversion—is never reached.

Rebuttal check: explicit `host="中国.icom.museum"` follows the same failing path. The client also supplies decoded hosts to this method during malformed-redirect recovery (`httpx/_client.py:514–515`).

Divergence: **L9**, lines 471–475: a supported Unicode hostname reaches an ASCII-only boundary before IDNA conversion. Valid URL edits fail instead of returning a URL.

Trigger:

```python
httpx.URL("https://中国.icom.museum/").copy_with(port=8443)
```

Expected: `https://xn--fiqs8s.icom.museum:8443/`. Derived actual consequence: `UnicodeEncodeError`.

Remedy: Immediately after line 465, add:

```python
if any(ord(char) > 127 for char in host):
    host = idna.encode(host, uts46=True).decode("ascii")
```

Dry-run: converts the triggering hostname before ASCII encoding; ASCII hosts and IPv6 handling retain their existing paths. Mentally checked only.

Verification: **Static evidence only.** The proposed remedy was not execution-verified against installed dependency versions.

### 🟡 Warning — [L4] Changing response encoding leaves previously decoded text cached

Premises: Documentation permits overriding the encoding after inspecting response text (`docs/quickstart.md:75–90`). Explicit encoding takes priority according to `Response.encoding`’s contract, lines 1333–1339. Existing override tests set encoding before the first `.text` access.

Trace:

1. `Response.text`, lines 1321–1327, decodes content and stores `_text`.
2. `TextDecoder` uses `errors="replace"` (`httpx/_decoders.py:247–248`), so invalid UTF-8 becomes a replacement character.
3. Assigning `response.encoding = "latin-1"` reaches the setter at lines 1348–1350, which changes only `_encoding`.
4. A subsequent `.text` access finds `_text` already present and returns it without decoding again.

Rebuttal check: no setter or other inspected path invalidates `_text`.

Divergence: **L4**, line 1350: changing the decoding configuration leaves cached output from the old configuration observable. `.encoding` and `.text` disagree.

Trigger:

```python
r = httpx.Response(
    200, content=b"\xff",
    headers={"Content-Type": "text/plain; charset=utf-8"},
)
first = r.text
r.encoding = "latin-1"
second = r.text
```

Expected `second`: `"ÿ"`. Derived actual value: `"\ufffd"`, unchanged from `first`.

Remedy: Replace the setter body with:

```python
self._encoding = value
self.__dict__.pop("_text", None)
```

Dry-run: the next access decodes the preserved bytes with the new encoding; setting encoding before first access remains valid. Mentally checked only.

Verification: **Static evidence only.** Neither reproduction nor remedy was executed.

### 🟡 Warning — [L6] QueryParams hashing disagrees with its equality semantics

Premises: Order-independent equality is explicitly tested (`tests/models/test_queryparams.py:40–42`). Hash-based deduplication is also supported (`test_queryparams_are_hashable`, lines 117–125). Equal hashable objects must have equal hashes.

Trace:

1. Constructing `a = QueryParams("a=1&b=2")` and `b = QueryParams("b=2&a=1")` retains different key insertion orders.
2. `__eq__`, lines 800–803, sorts both sets of pairs, so `a == b` is true.
3. `__str__`, lines 805–806, serializes pairs in insertion order.
4. `__hash__`, lines 797–798, consequently hashes different strings: `"a=1&b=2"` and `"b=2&a=1"`.

Rebuttal check: the existing set test covers matching serialization order only, so it does not defend this case.

Divergence: **L6**, line 798: hashing assumes serialization identifies equality, but equality discards ordering. Whenever the two string hashes differ, dictionaries and sets can treat equal objects as separate keys.

Trigger: With the `a` and `b` above, when their string hashes differ, `{a: "cached"}.get(b)` returns `None` instead of `"cached"`, and `len({a, b})` is two instead of one. Exact hash values depend on the interpreter’s hash seed.

Remedy: Replace line 798 with:

```python
return hash(tuple(sorted(self.multi_items())))
```

Dry-run: equal objects now hash the same canonical sequence, including duplicate pairs. Serialization order remains unchanged. Mentally checked only.

Verification: **Static evidence only.** No interpreter seed or dictionary lookup was exercised.

## Summary

The inspected paths contain silent query-data loss, failed Unicode URL edits, stale decoded text, and inconsistent hash behavior. All four are statically supported defects; none is execution-verified. No additional open lead is presented as a finding, and the omitted paths remain unassessed.