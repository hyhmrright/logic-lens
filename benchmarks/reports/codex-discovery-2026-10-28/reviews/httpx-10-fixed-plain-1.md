<!-- run 12d5a8a9173746a985fb1b553862a367; model gpt-6.1-sol; only temporary source links normalized -->

Found four defects supported by source inspection. The consequences below are derived from control flow; they were not verified by executing tests.

1. **[P2] Parsing query strings silently drops empty values.**  
   [QueryParams initialization](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L613) calls `parse_qs(value)` without `keep_blank_values=True`.

   **Expected:** `QueryParams("flag=")` preserves `flag` with an empty value, consistent with dictionary input. The supplied [tests explicitly support empty values](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L63).

   **Actual consequence:** String input produces no `flag` entry. This also changes request targets: constructing `Request("GET", "https://example.org/?flag=", params={"page": 2})` yields `?page=2`, losing the existing parameter. [Request construction](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L1094) merges through `URL.params`, which reparses the query using this constructor.

2. **[P2] `QueryParams` equality and hashing disagree about ordering.**  
   [Equality sorts all parameter pairs, while hashing uses the serialized string](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L797), whose order follows insertion order.

   **Expected:** Equal objects must have equal hashes. Order-independent equality is intentional: the [supplied test](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L40) equates dictionaries with reversed key order.

   **Actual consequence:** `QueryParams("a=1&b=2")` and `QueryParams("b=2&a=1")` compare equal but hash different strings. Unless those string hashes happen to collide, equivalent objects can occupy separate set entries or fail dictionary lookups. The existing hash test covers matching serialization order, so it misses this case.

3. **[P2] Copying an internationalized URL’s host or port raises `UnicodeEncodeError`.**  
   [Authority reconstruction](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L462) directly ASCII-encodes the hostname. When only the port changes, it obtains that hostname from `self.host`, which returns decoded Unicode for IDNA domains.

   **Expected:** `URL("https://中国.icom.museum").copy_with(port=8443)` retains the host and changes the port. Unicode host support is established by the [URL tests](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_url.py#L6).

   **Actual consequence:** Encoding `中国.icom.museum:8443` as ASCII raises before the rebuilt URL reaches IDNA normalization. Explicitly passing a Unicode `host` fails similarly. A supporting client path also passes `request.url.host` into `copy_with` when repairing a hostless redirect location, exposing the same failure for internationalized request hosts.

4. **[P2] Changing response encoding leaves previously decoded text stale.**  
   [The text property caches `_text`](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L1320), but the encoding setter only updates `_encoding`.

   **Expected:** An accepted encoding override should affect subsequent text decoding. The [quickstart documents overriding encoding](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/docs/quickstart.md#L85), including after examples that access `.text`.

   **Actual consequence:** For a response containing `b"\xff"` with `charset=utf-8`, first accessing `.text` caches `�`. Assigning `response.encoding = "latin-1"` then leaves `.text` returning `�` instead of `ÿ`, although `.encoding` reports `"latin-1"`. Iterating text again uses the new encoding, creating inconsistent results between text access methods. Existing override tests set encoding before accessing text.

**Open lead, not a confirmed defect:** Username/password copying uses `quote()` with its default slash allowance at lines 457–458. This warrants checking credentials containing `/`, but the downstream `rfc3986` parsing consequence was not established from supplied files. No specific failure or destination-change claim is made.

Verification was limited to static inspection of workspace source, tests, and documentation using nine shell calls. No files were modified, no external services or history were accessed, and no runtime or integration tests were run. The supplied tests were read as evidence, not executed.