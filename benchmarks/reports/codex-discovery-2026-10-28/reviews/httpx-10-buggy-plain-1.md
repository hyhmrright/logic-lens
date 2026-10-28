<!-- run 7bf4a7cee9bb438fbe33fb0b3b2f15f2; model gpt-6.1-sol; only temporary source links normalized -->

I found six defects supported by static inspection. The consequences below are traced from source; none were verified by execution.

1. **Blank query parameters are silently lost.**  
   At [_models.py:615](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L615), `QueryParams` calls `parse_qs(value)` without `keep_blank_values=True`.

   **Expected:** `QueryParams("a=&b=1")` preserves `a` with an empty value, consistent with dictionary input. Existing tests explicitly expect `QueryParams({"a": ""})` to serialize as `"a="` (`tests/models/test_queryparams.py:63`).

   **Actual consequence:** String input drops `a`. This also changes existing URLs when adding unrelated parameters: `URL("https://example.org/?a=").copy_add_param("b", "1")` loses `a=`, because URL parameter helpers parse and rebuild the entire query. The same path is used by `Request(..., params=...)`.

2. **Header updates discard all but the last repeated field.**  
   At [_models.py:965](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L965), `Headers.update()` assigns each incoming field through `self[key] = value`. That setter replaces existing occurrences of the same name.

   **Expected:** Updating with `[("Accept", "text/plain"), ("Accept", "application/json")]` retains both incoming values. `Headers` explicitly supports repeated fields, and `tests/models/test_headers.py:6` verifies their preservation during construction.

   **Actual consequence:** Only `"application/json"` survives. This affects ordinary request construction: `Client.build_request()` calls `_merge_headers()`, which uses this update method (`httpx/_client.py:399`). Repeated request headers therefore lose values before transport handling.

3. **Copying internationalized hosts can raise `UnicodeEncodeError`.**  
   At [_models.py:462](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L462), `copy_with()` obtains either the supplied host or `self.host`, then directly encodes it as ASCII.

   **Expected:** `URL("https://中国.icom.museum").copy_with(port=8443)` preserves the host and changes the port. Supplying a Unicode `host=` should likewise apply IDNA conversion. Unicode host support is explicitly tested in `tests/models/test_url.py:6`.

   **Actual consequence:** Both operations raise `UnicodeEncodeError` before reaching the URL constructor’s IDNA handling. Changing only the port is enough to trigger the failure because `self.host` returns decoded Unicode. The redirect repair path also supplies `request.url.host` to `copy_with()` (`httpx/_client.py:512`), exposing the same failure for an internationalized origin.

4. **Equal `QueryParams` objects can have different hashes.**  
   At [_models.py:797](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L797), hashing uses the serialized query in insertion order, while equality sorts all parameter pairs.

   **Expected:** Objects that compare equal must have equal hashes.

   **Actual consequence:** `QueryParams("a=1&b=2")` and `QueryParams("b=2&a=1")` compare equal but hash different strings. Their hashes can differ, causing dictionary lookups or set deduplication to fail for equivalent parameters. Equality across different key orders is intentional according to `tests/models/test_queryparams.py:40`; the hashability test at line 117 covers only matching serialization orders.

5. **IDNA decoding skips internationalized labels after an ASCII prefix.**  
   At [_models.py:246](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L246), `.host` invokes `idna.decode()` only when the entire hostname starts with `"xn--"`.

   **Expected:** `URL("https://www.xn--fiqs8s.icom.museum").host` returns `"www.中国.icom.museum"`, consistent with the property’s documented Unicode representation.

   **Actual consequence:** It returns `"www.xn--fiqs8s.icom.museum"` unchanged. Thus `.host` inconsistently exposes Unicode or punycode depending on the first label. The existing IDNA test cases all place the internationalized label first, leaving this case uncovered.

6. **Changing response encoding leaves previously decoded text stale.**  
   At [_models.py:1318](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L1318), `.text` caches `_text`. The encoding setter at line 1347 changes only `_encoding`.

   **Expected:** An accepted explicit encoding override affects subsequent text decoding. The documentation permits overriding encoding (`docs/quickstart.md:85`).

   **Actual consequence:** For a response containing `b"\xff"` with `charset=utf-8`, reading `.text` first caches a replacement character. Setting `response.encoding = "latin-1"` then leaves `.text` unchanged instead of returning `"ÿ"`. Meanwhile, `iter_text()` constructs a new decoder using the updated encoding, so the two text interfaces can disagree. Existing encoding tests set the override before the first `.text` access.

One **open lead, not a confirmed finding**, is credential escaping in `URL.copy_with()` at lines 457–458: `quote()` uses its default safe set, which leaves `/` unescaped in usernames and passwords. This could alter authority/path parsing, but the exact downstream result depends on `rfc3986` behavior that I did not verify within the supplied workspace.

Verification was limited to nine read-only shell calls examining workspace source, tests, and documentation. No files were modified, no external services or history were accessed, and no tests—including runtime integration tests—were run.