<!-- run cd6170b581594556b5cdc88b5863b4c7; model gpt-6.1-sol; only temporary source links normalized -->

**Mode:** Logic Review  
**Scope:** Targeted review of URL copying, query parsing/equality/hashing, and header merging in `httpx/_models.py`, with supporting client, transport, utility, documentation, and test paths. Response streaming and cookies were not deeply reviewed. Used 10 shell calls; no files changed.  
**Logic Score:** 79/100 — confirmed findings within this slice, with deductions capped per L-code per module.

Four defects are supported by static traces. None was runtime-verified; integration tests were excluded by the requested protocol.

**Findings**

**🟡 Warning — [L3] Blank query values disappear during parsing**

**Premises:** Empty query values are supported: `tests/models/test_queryparams.py:63–67` expects both `""` and `None` values to serialize as `a=`. The same tests establish equivalent string and mapping input forms.

**Trace:**

1. `Request("GET", "https://example.org/?a=", params={"b": "2"})` invokes `URL.copy_merge_params()` through `Request.__init__` at `_models.py:1092–1094`.
2. `URL.params` constructs `QueryParams` from the existing query string.
3. [QueryParams.__init__ line 615](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L615) calls `urllib.parse.parse_qs(value)` with its default `keep_blank_values=False`, producing `{}` for `"a="`.
4. Merging and reserialization produce `?b=2`.

Rebuttal check: the mapping-input path preserves blank values, but the URL-reading path necessarily uses string parsing.

**Divergence:** **L3:** line 615 discards a supported boundary value. Adding an unrelated parameter removes `a=` from the outgoing request target; the expected target is `/?a=&b=2`.

**Trigger:** The `Request(...)` expression above. Independently, `QueryParams("a=")` loses the key, while `QueryParams({"a": ""})` retains it.

**Remedy:** Replace line 615 with:

```python
self._dict = parse_qs(value, keep_blank_values=True)
```

Dry-run: retains `a=`, repeated blank values, and ordinary values; an empty query still produces no entries.

**Verification:** Static evidence only. Neither reproduction nor remedy was executed.

---

**🟡 Warning — [L6] Header merging drops every repeated value except the last**

**Premises:** `HeaderTypes` accepts sequences of pairs. `tests/models/test_headers.py:7–21` establishes preservation of repeated headers. Client configuration promises combined header values in `docs/advanced.md:100`, with request-level overrides demonstrated in `tests/client/test_headers.py:58–76`.

**Trace:**

1. `Client.build_request()` calls `_merge_headers()` at `_client.py:340`.
2. `_merge_headers()` copies client headers and invokes `Headers.update(headers)` at `_client.py:406–407`.
3. [Headers.update line 967](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L967) iterates incoming raw pairs, assigning each through `__setitem__`.
4. For `[("X-Tag", "one"), ("X-Tag", "two")]`, the second assignment replaces the first at line 1013. The transport receives only `"two"` through `request.headers.raw`.

Rebuttal check: constructing `Headers` directly preserves both values; the client’s mandatory merge introduces the loss.

**Divergence:** **L6:** `update()` uses a setter whose explicit contract removes duplicates. Expected request headers contain both incoming values, replacing any previous client values for that name; actual headers contain only the last incoming value.

**Trigger:** Pass the pair list above as `headers=` to `client.build_request("GET", "https://example.org/")`. Expected `get_list("X-Tag")`: `["one", "two"]`; actual: `["two"]`. Client initialization with repeated headers also traverses this update.

**Remedy:** Replace `Headers.update()`’s body with:

```python
headers = Headers(headers)
incoming = {key for _, key, _ in headers._list}
self._list = [
    item for item in self._list if item[1] not in incoming
]
self._list.extend(headers._list)
```

Dry-run: preserves incoming duplicates and raw bytes, replaces existing matching names case-insensitively, and retains unrelated headers. Updated names move to the end.

**Verification:** Static evidence only. Neither reproduction nor remedy was executed.

---

**🟡 Warning — [L9] Changing a port fails for internationalized hosts**

**Premises:** Internationalized hosts are supported; `tests/models/test_url.py:6–73` verifies Unicode `host` and IDNA `raw_host` representations. `copy_with()` accepts component changes, including `port`.

**Trace:**

1. `u = URL("https://中国.icom.museum/")` has Unicode `u.host`, as explicitly tested.
2. `u.copy_with(port=8443)` enters the authority reconstruction branch. Line 464 defaults the unchanged hostname to `self.host`.
3. The hostname contains no colon, so IPv6 handling does not alter it.
4. [Line 472](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L472) evaluates `f"{host}:{port}".encode("ascii")`, raising `UnicodeEncodeError`.

Rebuttal check: the final `URL(...)` constructor could encode an internationalized hostname, but execution fails before reaching it. Removing a port hits the same problem at line 474.

**Divergence:** **L9:** authority reconstruction treats the Unicode hostname as ASCII. Expected: a new URL with port `8443` and the same host. Actual: an exception for a supported URL.

**Trigger:** `URL("https://中国.icom.museum/").copy_with(port=8443)`. Explicitly supplying a Unicode `host=` also fails.

**Remedy:** Before constructing `kwargs["netloc"]`, insert:

```python
if any(ord(char) > 127 for char in host):
    host = idna.encode(host, uts46=True).decode("ascii")
```

Dry-run: converts the triggering hostname before ASCII serialization; ASCII hosts and IPv6 addresses retain their current paths.

**Verification:** Static evidence only. Neither reproduction nor remedy was executed.

---

**🟡 Warning — [L6] Equal query parameters can behave as different dictionary keys**

**Premises:** Equality deliberately ignores ordering: `tests/models/test_queryparams.py:40–42` compares differently ordered mappings as equal. Hash-based use is supported by `test_queryparams_are_hashable` at lines 117–125. Python requires equal objects to have equal hashes.

**Trace:**

1. Construct `a = QueryParams("a=1&b=2")` and `b = QueryParams("b=2&a=1")`.
2. `__eq__` sorts their pairs at `_models.py:803`, making `a == b` true.
3. [__hash__ line 798](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L798) hashes their serialized strings.
4. Serialization preserves insertion order, yielding different hash inputs: `"a=1&b=2"` and `"b=2&a=1"`.

Rebuttal check: existing hashability tests use matching serialization order, so they do not cover this mismatch.

**Divergence:** **L6:** hashing lacks equality’s normalization. Whenever the two string hashes differ, `{a: "value"}[b]` raises `KeyError`, and a set can retain both equal objects. A coincidental hash collision can mask the symptom.

**Trigger:** The two objects above, used interchangeably as dictionary keys or set members. Expected: one logical key/member.

**Remedy:** Replace the hash return expression with:

```python
return hash(tuple(sorted(self.multi_items())))
```

Dry-run: equal pair multisets now produce identical hash inputs, including repeated parameters.

**Verification:** Static evidence only; no process-specific hash values or collection behavior were measured.

**Summary**

The confirmed consequences are silent request-data loss, failure to copy supported internationalized URLs, and inconsistent hashed collection behavior. The score counts three distinct L-codes; the two L6 findings share one deduction under the supplied scoring rule. All remedies received static dry-runs only.

**Unresolved Investigations**

**U1 — IDNA labels after an ASCII subdomain:** `URL.host` decodes only when the entire hostname starts with `"xn--"` (`_models.py:246`). A hostname such as `www.xn--fiqs8s.icom.museum` may therefore violate the Unicode-host contract. The exact parser representation remains unchecked; next inspect the selected parser’s behavior for that input. This lead is excluded from Findings and the score.