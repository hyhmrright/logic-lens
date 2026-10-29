<!-- run 391fb7130448473aae06876e00d6c11d; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `httpx/_client.py`: URL construction and authentication/redirect handling, including sync and async implementations. Supporting URL, authentication, model, documentation, and test files inspected. Partial review; other behavior was not deeply traced.  
**Logic Score:** 79/100

Three defects are supported by concrete source traces. Consequences below are statically derived, not runtime observations. Six read-only shell calls were used; no files were modified, external services accessed, or integration tests run.

## Findings

### 🟡 Warning
**[L6] — A query in `base_url` absorbs the appended request path**

Premises: `URL.raw_path` includes both the path and query (`httpx/_urls.py:283–297`). Both client constructors accept a query-bearing base URL without rejecting it. `_merge_url` explicitly implements appending relative paths to the base path.

Trace: [1] Constructing a client with `base_url="https://example.org/api?mode=fast"` reaches [`_enforce_trailing_slash`](<[workspace]/httpx/_client.py:209>). Its input `raw_path` is `b"/api?mode=fast"`. [2] Line 212 appends `/` after the query, producing `/api?mode=fast/`. [3] Building a request for `"users"` reaches line 390, which appends `users`, producing `/api?mode=fast/users`. [4] `_urlparse.py:183–188` splits at the first `?`: the path remains `/api`, and `mode` becomes `fast/users`. Rebuttal check: PASSED — no constructor rejection, caller guard, or later path repair was found.

Divergence: L6 — these callers treat `raw_path` as a path-only component despite its actual contract. Expected request path: `/api/users`. Derived actual URL: `https://example.org/api?mode=fast/users`. This requests the wrong endpoint and changes a query value, regardless of the intended policy for retaining base queries.

Trigger: `Client(base_url="https://example.org/api?mode=fast", trust_env=False).build_request("GET", "users")`. The same construction applies to `AsyncClient`.

Remedy: Separate path and query before adding slashes or concatenating paths. A concrete policy is to preserve the base query unless the request supplies one. Replace `_enforce_trailing_slash`’s body with:

```python
path, separator, query = url.raw_path.partition(b"?")
if path.endswith(b"/"):
    return url
return url.copy_with(raw_path=path + b"/" + separator + query)
```

Replace lines 390–391 with:

```python
base_path, base_separator, base_query = (
    self.base_url.raw_path.partition(b"?")
)
path, separator, query = merge_url.raw_path.partition(b"?")
suffix = separator + query if separator else base_separator + base_query
return self.base_url.copy_with(
    raw_path=base_path + path.lstrip(b"/") + suffix
)
```

Dry-run: The trigger becomes `/api/users?mode=fast`; query-free construction and percent-encoded path bytes retain their existing behavior.

Verification: ⚠️ Unverified by execution — source trace only; runtime integration tests excluded by the requested protocol.

### 🟡 Warning
**[L4] — An authentication retry erases preceding redirect history**

Premises: Redirect history is accumulated by rebinding a local list, while authentication handling retains its own list. `docs/quickstart.md:442–444` promises followed redirects in history; `tests/client/test_auth.py:658–707` establishes that intermediate authentication responses also belong there.

Trace: [1] An authentication flow yields a request that receives redirect response A, then authentication challenge B. [2] [`_send_handling_redirects`](<[workspace]/httpx/_client.py:977>) rebinds `history` at line 1002, so B has `history=[A]`, but the authentication caller still holds `[]`. [3] If the auth flow yields another request, line 966 overwrites B’s history with that empty caller list. [4] Line 969 appends only B; the eventual final response C therefore has `[B]`. The async implementation repeats this sequence at lines 1715–1718 and 1752. Rebuttal check: PASSED — multi-request authentication is explicitly supported; no subsequent merge restores A.

Divergence: L4 — the mutation at line 966 discards already-recorded history. Expected final history: `[A, B]`; derived actual history: `[B]`. B’s own history is also incorrectly cleared. This is a sequential state bug and requires no concurrent execution.

Trigger: Use `follow_redirects=True` and a custom `Auth.auth_flow` that yields `GET /start`, then yields `response.request` once more. Return `302 Location: /login` for `/start`, then `401` and `200` for successive `/login` requests. Expected final history statuses: `[302, 401]`; actual by trace: `[401]`.

Remedy: In both authentication handlers, replace `response.history = list(history)` at lines 966 and 1715 with:

```python
history = list(response.history)
```

Keep the subsequent `history.append(response)`. Dry-run: B retains `[A]`; the caller accumulates `[A, B]`; authentication without redirects preserves its existing history behavior.

Verification: ⚠️ Unverified by execution — source trace only; runtime integration tests excluded by the requested protocol.

### 🟡 Warning
**[L3] — Authentication challenges incorrectly consume the redirect allowance**

Premises: `_client.py:614–615` defines `max_redirects` as the maximum number of redirect responses followed. Digest authentication legitimately yields a second request after a 401 (`httpx/_auth.py:193–222`).

Trace: [1] Configure `max_redirects=0` and issue a request using fresh `DigestAuth`. [2] A valid 401 Digest challenge causes the auth flow to yield an authenticated retry. [3] Authentication handling appends that 401 to `history` at line 969. [4] On entering [`_send_handling_redirects`](<[workspace]/httpx/_client.py:984>) again, `len(history) > self.max_redirects` evaluates as `1 > 0`; it raises before sending the retry. Async lines 1718 and 1733 behave identically. Rebuttal check: PASSED — zero redirects does not prohibit authentication negotiation, and neither the guard nor caller distinguishes 401 responses from redirects.

Divergence: L3 — the guard counts authentication responses against a redirect-only boundary. Expected: send the authenticated retry and return the server’s response. Derived actual behavior: raise `TooManyRedirects` after following zero redirects. This also occurs with `follow_redirects=False`.

Trigger: Configure `max_redirects=0`, `auth=DigestAuth("u", "p")`; return `401` with `WWW-Authenticate: Digest realm="r", nonce="n", qop="auth"` initially, and `200` for the authenticated retry.

Remedy: Replace the guard at lines 984 and 1733 with:

```python
if follow_redirects and sum(
    response.has_redirect_location for response in history
) > self.max_redirects:
```

Apply the preceding history fix as well so earlier redirect chains remain available for counting. Dry-run: a 401 contributes zero; a followed redirect contributes one; exceeding the configured redirect allowance still raises.

Verification: ⚠️ Unverified by execution — source trace only; runtime integration tests excluded by the requested protocol.

## Summary

Prioritize the URL construction defect because it changes the requested endpoint. Address the two history-related defects together: preserve accumulated responses and count only redirects toward the redirect limit.

No speculative open leads are counted as defects or score deductions. Transport lifecycle, cancellation, proxy setup, and remaining client behavior were outside this focused review; the inspected tests were evidence, not executed validation.