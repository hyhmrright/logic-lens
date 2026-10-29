<!-- run 71853ae3fbf242878a499b5e92d0d7db; model gpt-6.1-sol; only temporary source links normalized -->

I found four concrete defects through static inspection. The consequences below are derived from source; they were not runtime observations.

1. **URL component updates fail for internationalized hostnames.**  
   [URL.copy_with, line 464](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L464) takes the decoded Unicode `self.host` when changing a port, then encodes it directly as ASCII.

   For example, `URL("https://中国.icom.museum").copy_with(port=8443)` should preserve the hostname and change the port. Instead, it raises `UnicodeEncodeError` before constructing the new URL. Explicitly passing a Unicode `host=` also fails. The existing [IDNA tests](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_url.py#L6) establish that these hostnames are supported and `.host` returns Unicode. The update path needs IDNA conversion rather than direct ASCII encoding.

2. **Parsing query strings silently removes empty-valued parameters.**  
   [QueryParams.__init__, line 615](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L615) calls `parse_qs(value)` without `keep_blank_values=True`. Consequently, `QueryParams("a=&b=1")` contains only `b`, although constructing from `{"a": "", "b": "1"}` retains both parameters. The [existing tests](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L63) explicitly expect empty values to serialize as `a=`.

   This also changes request targets: adding `params={"c": "2"}` to a request URL ending in `?a=&b=1` rebuilds the query as `?b=1&c=2`, losing `a`. Expected behavior is to preserve the existing empty parameter while adding `c`.

3. **Equal `QueryParams` objects can have different hashes.**  
   [QueryParams.__hash__ and __eq__, line 797](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L797) use incompatible representations: equality sorts parameter pairs, while hashing uses their insertion-order serialization.

   Thus `QueryParams("a=1&b=2")` and `QueryParams("b=2&a=1")` compare equal but hash different strings. This violates the requirement that equal objects have equal hashes; sets can retain both objects, and dictionary lookups using an equal object can miss. The [tests establish order-independent equality](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L40) and separately [expect hashability](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_queryparams.py#L117), but do not cover their interaction.

4. **Header updates discard repeated values from the incoming headers.**  
   [Headers.update, line 965](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L965) assigns each incoming raw pair using `self[key] = value`. That setter removes duplicate entries, so each repeated incoming name overwrites its previous value.

   For example, updating with `[("Accept", "text/plain"), ("Accept", "application/json")]` leaves only `application/json`. Expected behavior for this multidict is to replace the old values with both incoming values, preserving the incoming header collection. The [header tests](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/tests/models/test_headers.py#L8) establish duplicate preservation. This affects ordinary request construction because [Client._merge_headers](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_client.py#L399) calls this update method; earlier supplied values never reach the constructed request.

**Open lead:** [Credential quoting in URL.copy_with](https://github.com/encode/httpx/blob/8dc9b6bd59114439128d23a60609bee09daf508c/httpx/_models.py#L457) uses `quote()` with its default slash-preserving behavior. A username or password containing `/` therefore introduces an unescaped path delimiter into the assembled authority. The quoting problem is visible, but the precise final parsing or exception behavior depends on `rfc3986`; I have not established that consequence from workspace evidence and am not counting it among the confirmed findings.

Verification was limited to eight read-only shell calls within the supplied workspace. No files were modified, external services or history accessed, or tests executed. Runtime integration behavior remains unverified.