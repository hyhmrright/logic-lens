<!-- run 0691b3a182fd43f6b8fdf6d38b85219c; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces of `httpx/_models.py`: query parsing, equality/hashing, URL copying, and response cleanup; supporting client code, types, utilities, documentation, and model tests. Ten shell calls used. Headers, cookies, and async lifecycle paths were not exhaustively reviewed.  
**Logic Score:** 79/100

Three defects are supported by static evidence. No runtime tests were run; consequences below are derived from code and supported contracts. No files were modified.

## Findings

### 🟡 Warning — [L3] Blank query values disappear during parsing and merging

**Premises:** Empty values are supported: [test_queryparams.py:63](tests/models/test_queryparams.py:63) requires `{"a": ""}` to serialize as `a=`. String and mapping inputs are both accepted representations, and URL merging must preserve unrelated parameters ([test_url.py:151](tests/models/test_url.py:151)).

**Trace:**

1. `Request("GET", "https://example.org/?a=", params={"b": "1"})` calls `URL.copy_merge_params()` at [\_models.py:1096](httpx/_models.py:1096).
2. That method reads `self.params`, which constructs `QueryParams` from the existing query.
3. At [\_models.py:615](httpx/_models.py:615), `parse_qs(value)` uses its default `keep_blank_values=False`, so `"a="` becomes `{}`.
4. Merging adds only `b=1`; serialization produces `https://example.org/?b=1`.

Rebuttal check: mapping inputs preserve empty strings, but the string-parsing branch has no corresponding preservation step.

**Divergence:** **L3:** parsing treats a present parameter with an empty value as absent. Expected: `?a=&b=1`. Actual code-derived result: `?b=1`, changing the outgoing request’s parameters.

**Trigger:** The `Request(...)` call above. Directly, `QueryParams("a=")` also loses `"a"`, unlike `QueryParams({"a": ""})`.

**Remedy:** At line 615, replace the assignment with:

```python
self._dict = parse_qs(value, keep_blank_values=True)
```

Dry-run, static only: preserves empty values, including repeated ones, while retaining existing nonempty parsing behavior.

**Verification:** Static evidence only. Runtime reproduction and remedy testing were excluded by the discovery protocol.

### 🟡 Warning — [L9] Changing an internationalized URL’s port raises an encoding error

**Premises:** Internationalized hosts are supported; [test_url.py:25](tests/models/test_url.py:25) establishes that `https://faß.de` exposes host `"faß.de"`. `copy_with()` accepts component changes, and [test_url.py:89](tests/models/test_url.py:89) exercises changing the port while preserving the host.

**Trace:**

1. `URL("https://faß.de").copy_with(port=8443)` enters the host/port branch.
2. [\_models.py:464](httpx/_models.py:464) defaults the omitted host to `self.host`. That property returns decoded Unicode via `idna.decode()` at line 247.
3. The IPv6 branch does not apply.
4. [\_models.py:472](httpx/_models.py:472) evaluates `"faß.de:8443".encode("ascii")`, which raises `UnicodeEncodeError`.

Rebuttal check: the final `URL(...)` reconstruction cannot normalize the hostname because execution fails before reaching it.

**Divergence:** **L9:** the decoded host is encoded directly as ASCII instead of being converted back to IDNA. Expected: an equivalent URL with port 8443. Actual: an exception. Explicitly supplying a Unicode `host=` encounters the same problem.

**Trigger:** `httpx.URL("https://faß.de").copy_with(port=8443)`.

**Remedy:** Immediately after line 465, insert:

```python
if any(ord(char) > 127 for char in host):
    host = idna.encode(host, uts46=True).decode("ascii")
```

Dry-run, static only: converts `"faß.de"` to `"xn--fa-hia.de"` before ASCII encoding; ASCII names and IPv6 retain their existing paths.

**Verification:** Static evidence only. Runtime reproduction and remedy testing were excluded.

### 🟡 Warning — [L6] Equal query parameters can have different hashes

**Premises:** Parameter equality deliberately ignores ordering ([test_queryparams.py:40](tests/models/test_queryparams.py:40)). Hashability and set deduplication are also supported ([test_queryparams.py:117](tests/models/test_queryparams.py:117)). Equal hashable objects must have equal hashes.

**Trace:**

1. Construct `a = QueryParams("a=1&b=2")` and `b = QueryParams("b=2&a=1")`.
2. [\_models.py:803](httpx/_models.py:803) sorts both item lists, so `a == b` evaluates to `True`.
3. Serialization preserves their differing parameter order.
4. [\_models.py:798](httpx/_models.py:798) therefore hashes two different strings: `"a=1&b=2"` and `"b=2&a=1"`.

Rebuttal check: the existing set test covers equivalent inputs with identical serialized order; it does not cover reordered equal objects.

**Divergence:** **L6:** the hash implementation violates the contract required by dictionary/set consumers. Expected: interchangeable equal keys and one set entry. Actual: hashes can differ, allowing duplicate equal set entries or failed dictionary lookup through an equal key.

**Trigger:** Use the two objects above in `{a, b}` or retrieve `{a: "value"}[b]`. The erroneous outcome depends on the runtime hashes; an accidental collision can mask it.

**Remedy:** Replace the return expression in `QueryParams.__hash__` with:

```python
return hash(tuple(sorted(self.multi_items())))
```

Dry-run, static only: hashing now uses the same ordering normalization as equality and preserves duplicate multiplicity.

**Verification:** Static evidence only. No runtime hash values or container outcomes were measured.

## Summary

Preserve blank query values, encode Unicode hosts before constructing the authority, and make query hashing consistent with equality. The score reflects three confirmed findings in this inspected slice, not whole-project correctness or shipping safety.

## Unresolved Investigations

- **Userinfo escaping:** Lines 457–458 call `quote()` with its default slash allowance. Credentials containing `/` may produce a malformed authority. The resulting `rfc3986` rejection or reinterpretation was not established from supplied evidence, so this is **not a confirmed finding**. Next check: trace the dependency’s authority reconstruction or run an authorized isolated probe with `username="a/b"`.