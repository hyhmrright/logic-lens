<!-- run 8830f5a44fe940d4b4486fd47d8098f2; model gpt-6.1-sol; only temporary source links normalized -->

Found five defects supported by static code paths. The examples below are source-derived consequences, not runtime observations.

1. **Blank query values are silently discarded.**  
   [httpx/_models.py:615](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L615) calls `parse_qs(value)` without `keep_blank_values=True`.

   **Expected:** Parsing `flag=&x=1` preserves `flag` with an empty value.  
   **Actual consequence:** `QueryParams("flag=&x=1")` contains only `x`. Constructing a request with that URL and additional `params` also removes `flag`, because request construction parses and merges the existing query through `URL.params`.

   This conflicts with [tests/models/test_queryparams.py:63](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L63), which establishes that empty values are valid and serialize as `a=`. Bare parameters such as `?flag` are also dropped.

2. **Equal `QueryParams` objects can have different hashes.**  
   [httpx/_models.py:797](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L797) hashes `str(self)`, whose serialization preserves insertion order. Equality immediately below compares sorted parameter pairs.

   **Expected:** Equal objects have equal hashes.  
   **Actual consequence:** `QueryParams("a=1&b=2")` and `QueryParams("b=2&a=1")` compare equal but hash different serialized strings. Consequently, equal objects can occupy separate set entries or fail dictionary lookups.

   [tests/models/test_queryparams.py:40](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L40) explicitly establishes order-independent equality. The hashability test covers identical ordering only.

3. **Copying an internationalized URL’s port raises `UnicodeEncodeError`.**  
   [httpx/_models.py:462](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L462) rebuilds the authority whenever `host` or `port` changes. It defaults to `self.host`, which returns Unicode for internationalized domains, then directly encodes that hostname as ASCII.

   **Expected:** `URL("https://中国.icom.museum").copy_with(port=444)` preserves the hostname and changes the port.  
   **Actual consequence:** The ASCII conversion raises `UnicodeEncodeError`. Supplying `host="中国.icom.museum"` directly fails through the same path.

   [tests/models/test_url.py:67](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_url.py#L67) establishes Unicode hostname support, while its port-copy test uses an ASCII hostname. The copying path needs IDNA encoding before creating ASCII authority bytes.

4. **Unicode hostname decoding fails when the internationalized label follows an ASCII label.**  
   [httpx/_models.py:246](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L246) calls `idna.decode(host)` only when the entire hostname starts with `xn--`.

   **Expected:** `URL("https://www.xn--fiqs8s.icom.museum").host` returns `www.中国.icom.museum`, consistent with the property’s documented Unicode representation.  
   **Actual consequence:** It returns `www.xn--fiqs8s.icom.museum` unchanged. Adding an ASCII subdomain therefore changes whether `.host` decodes the internationalized portion.

   Existing IDNA tests cover hostnames whose first label is internationalized, leaving this branch uncovered.

5. **Changing response encoding leaves previously decoded text stale.**  
   [httpx/_models.py:1320](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L1320) caches `.text` in `_text`. The encoding setter at line 1349 changes `_encoding` without invalidating that cache.

   **Expected:** Setting an explicit encoding makes subsequent text access use it, as the documented encoding override promises.  
   **Actual consequence:** For a response containing `b"\xff"` with `charset=utf-8`, accessing `.text` caches `"\ufffd"`. Setting `.encoding = "latin-1"` afterward still returns `"\ufffd"` instead of `"ÿ"`. Calling `iter_text()` then decodes using the new encoding, so the two text interfaces disagree.

   [tests/models/test_responses.py:276](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_responses.py#L276) tests overriding encoding before the first text access, which avoids the defect.

No additional open leads are reported. Verification was limited to static inspection using eight read-only shell calls. No runtime or integration tests were run; no files were modified, and no external services or repository history were accessed.