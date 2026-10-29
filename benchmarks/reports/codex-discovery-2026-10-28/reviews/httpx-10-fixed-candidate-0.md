<!-- run 6e56039c01ae4c1d965203cca6932474; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces in `httpx/_models.py`: query parsing, equality/hashing, URL authority changes, hostname decoding, and response text caching. Supporting evidence: model tests, client request/redirect handling, transport code, decoders, and documentation. Eight read-only tool calls; no history, external services, or file modifications. This was not exhaustive coverage of streaming, headers, or cookies.  
**Logic Score:** 72/100

Six defects are supported by static traces. Runtime integration tests were excluded by the requested protocol; reproductions and remedies below were not executed.

## Findings

### 🟡 Warning

**[L3] — Query parsing silently removes empty-valued parameters**

Premises: Empty query values are supported: `tests/models/test_queryparams.py:63–67` requires both `""` and `None` to serialize as `a=`. URL parameter merging must preserve unrelated existing parameters, as exercised at `tests/models/test_url.py:151–156`.

Trace: 1. `Request("GET", "https://example.org/?a=", params={"b": "1"})` enters `Request.__init__`, which merges parameters. 2. `URL.params` constructs `QueryParams("a=")`. 3. [The constructor](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L615) calls `parse_qs` without `keep_blank_values=True`, producing an empty dictionary. 4. Merging adds only `b`; serialization produces `https://example.org/?b=1`. Rebuttal check: neither the merge nor the transport restores the discarded parameter.

Divergence: L3 at line 615: a supported empty value disappears. The outgoing request changes meaning when another parameter is added.

Trigger: The request above should retain `?a=&b=1`; the code instead constructs `?b=1`.

Remedy: Replace line 615 with `self._dict = parse_qs(value, keep_blank_values=True)`. Mental dry-run preserves empty values and leaves ordinary nonempty parsing unchanged.

Verification: Static evidence only; execution excluded.

**[L9] — Changing a port fails for internationalized hostnames**

Premises: Unicode hostnames are supported and `.host` returns Unicode (`tests/models/test_url.py:6–73`). Port replacement is supported (`tests/models/test_url.py:89`).

Trace: 1. Construct `URL("http://中国.icom.museum/")`. 2. Calling `.copy_with(port=8080)` takes the existing decoded `.host` at line 464. 3. [Authority construction](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L471) directly ASCII-encodes `"中国.icom.museum:8080"`. 4. That raises `UnicodeEncodeError` before the URL constructor can apply IDNA encoding. Rebuttal check: initial URL normalization cannot protect a subsequently decoded hostname.

Divergence: L9 at line 472: changing only the port crashes for an otherwise supported URL.

Trigger: `httpx.URL("http://中国.icom.museum/").copy_with(port=8080)` should return the same hostname with port 8080; it raises instead.

Remedy: Before line 467, insert:

```python
if host and any(ord(char) > 127 for char in host):
    host = idna.encode(host, uts46=True).decode("ascii")
```

Mental dry-run converts the Unicode hostname before ASCII serialization; ASCII and IPv6 inputs retain their existing paths.

Verification: Static evidence only; execution excluded.

**[L6] — Equal query parameters can behave as different dictionary keys**

Premises: Equality intentionally ignores parameter ordering (`tests/models/test_queryparams.py:40–42`). Hashability and set deduplication are supported at lines 117–125 of that test file. Equal hashable objects must have equal hashes.

Trace: 1. Construct `a = QueryParams("a=1&b=2")` and `b = QueryParams("b=2&a=1")`. 2. `__eq__` sorts their pairs, so `a == b`. 3. [Their hashes](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L797) use their unsorted serialized strings, which differ. 4. Whenever those string hashes differ, dictionary lookup using the equal alternate representation misses. Rebuttal check: serialization preserves insertion order; it performs no canonicalization.

Divergence: L6: the hashing implementation violates the contract required by dictionary/set consumers. Equal instances can occupy separate set entries or miss cached values.

Trigger: With the objects above, `{a: "cached"}[b]` can raise `KeyError` despite `a == b`. Exact hash values depend on the interpreter’s hash seed.

Remedy: In `QueryParams.__hash__`, replace line 798 with `return hash(tuple(sorted(self.multi_items())))`. Mental dry-run uses the same canonical pairs as equality, including duplicate values.

Verification: Static evidence only; no particular hash seed was executed.

**[L4] — An encoding override leaves previously decoded text stale**

Premises: Explicit response encoding overrides are supported by `docs/quickstart.md:85–89` and `tests/models/test_responses.py:276–299`; no restriction to setting them before reading `.text` is stated.

Trace: 1. Construct a response containing `b"\xff"` with `Content-Type: text/plain; charset=utf-8`. 2. Reading `.text` caches the replacement character `"�"`. 3. [Setting `.encoding`](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L1349) to `"latin-1"` changes only `_encoding`. 4. Subsequent `.text` access returns `_text` without decoding again. Rebuttal check: the setter neither invalidates the cache nor rejects the operation.

Divergence: L4: `.encoding` reports Latin-1 while `.text` still reflects UTF-8 decoding.

Trigger: Read `.text`, assign `response.encoding = "latin-1"`, then read `.text` again. Expected `"ÿ"`; the code returns `"�"`.

Remedy: After line 1350, add `self.__dict__.pop("_text", None)`. Mental dry-run forces the next access to decode with the new encoding; assignment before the first access remains valid.

Verification: Static evidence only; execution excluded.

**[L6] — Credential setters leave `/` unescaped**

Premises: Username/password setters accept decoded strings and escape them, with round-trip expectations demonstrated in `tests/models/test_url.py:254–264`.

Trace: 1. Call `URL("https://example.org").copy_with(username="a/b")`. 2. [Line 457](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L457) calls `urllib.parse.quote` with its default `safe="/"`, preserving the slash. 3. Authority assembly produces `a/b@example.org`. 4. Reparsing `https://a/b@example.org` treats `a` as the hostname and `/b@example.org` as the path. Rebuttal check: quoting occurs before authority assembly, with no subsequent credential-specific escaping.

Divergence: L6: path-oriented quoting defaults corrupt an authority component, changing the destination hostname.

Trigger: The call above should produce `https://a%2Fb@example.org`; it constructs a URL targeting host `a`.

Remedy: At lines 457 and 458, pass `safe=""` to both `quote` calls. Apply the same change to `quote(self.username)` at line 592, where representation rebuilding has the same issue. Mental dry-run escapes `/` while preserving ordinary credential round trips.

Verification: Static evidence only; execution excluded.

**[L9] — IDNA decoding misses internationalized labels after a subdomain**

Premises: `.host` promises Unicode internationalized domain names; `.raw_host` supplies their encoded representation (`_models.py:221–265`).

Trace: 1. Construct `URL("https://www.xn--fiqs8s.icom.museum/")`. 2. [The `.host` getter](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L246) tests whether the entire hostname starts with `"xn--"`. 3. The `"www."` prefix makes that false, so decoding is skipped and the encoded hostname is returned. Rebuttal check: `.host` has no later decoding stage.

Divergence: L9: the accessor returns Punycode where its contract requires Unicode.

Trigger: The URL above should have `.host == "www.中国.icom.museum"`; the getter returns `"www.xn--fiqs8s.icom.museum"`.

Remedy: Replace line 246 with `if any(label.startswith("xn--") for label in host.split(".")):`. Mental dry-run detects encoded labels at any position; ordinary ASCII hosts and IPv6 literals skip decoding.

Verification: Static evidence only; execution excluded.

## Summary

Prioritize silent parameter loss and credential corruption because both alter request semantics. The score reflects confirmed findings within this inspected slice, with deductions capped per L-code for the module; it does not measure whole-project correctness. No source changes or runtime verification were performed.