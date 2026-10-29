<!-- run 491d57a90e6148efadbdb954f573c327; model gpt-6.1-sol; only temporary source links normalized -->

Found four concrete defects supported by static inspection. The consequences below are source-derived predictions; no runtime tests were run.

1. **[P2] Parsing query strings silently drops empty values.**  
   [`QueryParams.__init__`](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L615) calls `parse_qs(value)` without `keep_blank_values=True`, so `QueryParams("flag=&keep=1")` loses `flag`.

   **Expected:** preserve `flag` with an empty value, consistent with the dictionary constructor. Local [tests explicitly expect empty values to serialize as `a=`](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L63).

   **Consequence:** adding unrelated request parameters can remove existing ones. For example, `Request("GET", "https://example.org/?flag=&keep=1", params={"x": "2"})` produces a query equivalent to `keep=1&x=2`, losing `flag=`. The [request constructor](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L1095) invokes `copy_merge_params`, which reparses the existing query through `QueryParams`.

2. **[P2] Changing the port of an internationalized URL raises `UnicodeEncodeError`.**  
   In [`URL.copy_with`](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L462), changing either `host` or `port` rebuilds the authority using `self.host`, then directly encodes it as ASCII. `self.host` deliberately returns Unicode for internationalized names.

   **Expected:** `URL("https://中国.icom.museum").copy_with(port=8443)` returns the same host with port 8443.

   **Consequence:** ASCII encoding fails before URL construction can apply IDNA encoding. Explicitly passing a Unicode hostname to `copy_with(host=...)` fails through the same path. Local [URL tests establish support for this internationalized hostname](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_url.py#L10).

3. **[P2] Equal `QueryParams` objects can have different hashes.**  
   [`__eq__`](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L800) compares sorted parameter pairs, while [`__hash__`](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L797) hashes their order-preserving serialization.

   **Expected:** objects comparing equal must have equal hashes.

   **Consequence:** `QueryParams("a=1&b=2")` and `QueryParams("b=2&a=1")` compare equal but hash different strings. Unless those string hashes happen to collide, a set retains both objects, and dictionary lookup using the equal alternate object can miss. The existing [hashability test](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L117) checks equivalent constructor forms but does not exercise reordered parameters.

4. **[P3] `URL.host` leaves internationalized labels encoded when they follow an ASCII label.**  
   [`URL.host`](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L246) invokes `idna.decode` only when the entire hostname starts with `"xn--"`.

   **Expected:** `URL("http://www.xn--fiqs8s.icom.museum").host` returns `"www.中国.icom.museum"`, following the property's documented Unicode representation.

   **Consequence:** it returns `"www.xn--fiqs8s.icom.museum"` unchanged because the first label is `www`. Applications displaying or comparing `.host` receive inconsistent representations depending on which label contains internationalized characters.

No additional open leads are presented as findings. Verification was limited to seven targeted, read-only shell calls within the supplied workspace. No files were modified, no external services or history were accessed, and no unit or runtime integration tests were executed.