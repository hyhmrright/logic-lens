<!-- run 7fc958e3cc274084bc99f8b99f053339; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted review of `httpx/_models.py`: `URL.copy_with`, `QueryParams.__init__`, and `QueryParams.__hash__`, including supporting getters, equality, callers, and tests. Other functionality was not exhaustively reviewed.  
**Logic Score:** 86/100

> Three defects are supported by static traces. Runtime behavior and proposed remedies were not executed.

The reviewed paths should preserve query-parameter values, support internationalized hostnames when copying URLs, and maintain consistent equality and hashing.

## Findings

### 🟡 Warning
**[L6] — Parsing query strings silently discards empty-valued parameters**

Premises: `QueryParamTypes` explicitly accepts strings, bytes, and mappings. Mapping construction preserves empty values; `tests/models/test_queryparams.py:63–67` explicitly expects both `""` and `None` to serialize as `a=`.

Trace: [1] At [constructor line 615](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L615), string input `"a=&b=2"` reaches `urllib.parse.parse_qs(value)` without `keep_blank_values=True`. [2] Its default behavior drops `a`, producing `{"b": ["2"]}`. [3] `multi_items()` and `__str__()` consequently serialize only `b=2`. [4] This affects request construction: `Request.__init__:1096` calls `copy_merge_params`, which parses existing URL parameters through `URL.params:348` before rebuilding the query. Rebuttal check: PASSED — these public paths contain no guard or restoration of discarded values.

Divergence: **L6:** the parser’s default contract conflicts with the model’s supported empty-value representation. Reading `.params` loses information; adding unrelated parameters can remove existing parameters from the resulting request URL.

Trigger: `httpx.Request("GET", "https://example.org/?a=&b=2", params={"c": "3"})`. Expected query: `a=&b=2&c=3`. Static trace yields: `b=2&c=3`. Likewise, `QueryParams("a=")` becomes empty, unlike `QueryParams({"a": ""})`.

Remedy: Replace line 615 with `self._dict = parse_qs(value, keep_blank_values=True)`. Dry-run: ✅ `a` becomes `[""]`, merging retains it, and serialization emits `a=`; nonempty parameters and genuinely empty input retain their behavior.

Verification: ⚠️ Unverified — execution was omitted under the requested discovery protocol.

### 🟡 Warning
**[L9] — Changing a port on an internationalized hostname raises `UnicodeEncodeError`**

Premises: `URL.host` deliberately returns decoded Unicode, whereas `URL.raw_host` returns ASCII IDNA bytes. Internationalized hostname support is explicitly exercised in `tests/models/test_url.py:6–73`. `copy_with` accepts independently supplied host and port components.

Trace: [1] `URL("https://faß.de").host` returns `"faß.de"` through IDNA decoding at `_models.py:246–247`. [2] Calling `copy_with(port=8443)` enters the host/port branch and defaults `host` to `self.host` at line 464. [3] At [line 472](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L472), `"faß.de:8443".encode("ascii")` raises before the URL constructor at line 537 can perform IDNA conversion. Rebuttal check: PASSED — the argument types are accepted, and no hostname conversion or exception recovery precedes this expression.

Divergence: **L9:** an already valid internationalized URL cannot have its port changed. Explicitly supplying a Unicode `host` fails for the same reason. Expected behavior is an equivalent URL with the requested component changed; the traced consequence is `UnicodeEncodeError`.

Trigger: `httpx.URL("https://faß.de").copy_with(port=8443)`. Expected: `https://xn--fa-hia.de:8443`. Static trace: `UnicodeEncodeError`.

Remedy: Immediately after line 465, insert:
```python
if any(ord(char) > 127 for char in host):
    host = idna.encode(host, uts46=True).decode("ascii")
```
Dry-run: ✅ the hostname becomes `xn--fa-hia.de`, the port is appended, and ASCII encoding succeeds. Existing ASCII hostnames and IPv6 inputs bypass the addition.

Verification: ⚠️ Unverified — execution was omitted under the requested discovery protocol.

### 🟡 Warning
**[L6] — Equal query parameters can have unequal hashes**

Premises: `QueryParams.__eq__` compares sorted parameter pairs, making equality independent of insertion order. Tests at `tests/models/test_queryparams.py:40–42` explicitly require reordered mappings to compare equal. Equal hashable objects must have equal hashes.

Trace: [1] Construct `a = QueryParams("x=1&y=2")` and `b = QueryParams("y=2&x=1")`; their dictionaries preserve different insertion orders. [2] `__eq__:803` sorts both pair lists, so `a == b` is true. [3] `__str__:806` preserves their different orders, producing `"x=1&y=2"` and `"y=2&x=1"`. [4] [__hash__ line 798](https://github.com/encode/httpx/blob/321d4aa5097fe7f24cdfed7191c44de589294780/httpx/_models.py#L798) hashes those different strings without canonicalization. Rebuttal check: PASSED — construction does not canonicalize ordering; the hashability test at lines 117–125 covers identical orderings only. Accidental hash collisions do not enforce the required invariant.

Divergence: **L6:** hashing does not respect the equality contract. When the two string hashes differ, a dictionary keyed by `a` cannot be looked up using equal object `b`, and a set can retain both.

Trigger: With `a` and `b` above, evaluate `{a: "value"}[b]`. Expected: `"value"`. Predicted consequence when their hashes differ: `KeyError`. No process-specific hash values were measured.

Remedy: Replace line 798 with `return hash(tuple(sorted(self.multi_items())))`. Dry-run: ✅ both objects produce the same sorted tuple and hash; duplicate pairs remain represented, and serialization order stays unchanged.

Verification: ⚠️ Unverified — execution was omitted under the requested discovery protocol.

## Summary

Prioritize preserving empty-valued query parameters because ordinary request construction can silently alter the outgoing URL. The score applies one deduction per unique risk code, as required by the supplied framework.

**Open lead:** `URL.copy_with:457–458` uses `quote()` with its default slash-safe behavior for usernames and passwords. A value such as `"a/b"` therefore places an unescaped slash inside the assembled authority. The eventual parser consequence remains unconfirmed because the external `rfc3986` implementation was outside the supplied workspace.

Seven read-only shell calls were used. No files were modified, no external services or history were accessed, and no runtime tests were run. Consequences above are static predictions, not execution observations.