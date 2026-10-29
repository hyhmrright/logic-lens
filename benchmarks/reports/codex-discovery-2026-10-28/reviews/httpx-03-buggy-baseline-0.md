<!-- run 76438d988ddc447dbd055949e1a8a799; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Partial review of `httpx/_client.py`: `send`, authentication handling, and redirect handling in both clients; supporting models, transports, auth, docs, and tests.
**Logic Score:** 79/100

> Three defects are supported by source traces. Runtime behavior was not tested.

## Findings

### 🟡 Warning
**[L3] — Authentication responses incorrectly consume the redirect allowance**

Premises: `max_redirects` limits followed redirect responses (`_client.py:605`). Digest authentication can yield a second request after a 401 (`_auth.py:199–222`). Authentication responses also enter `history`.

Trace: [1] An initial Digest request receives 401 without any redirect. [2] `_send_handling_auth` appends that response to `history` at line 958. [3] The retry enters [the redirect handler](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L973), where `len(history) > max_redirects` raises before sending it. The async implementation repeats this at lines 1705 and 1720. Rebuttal check: PASSED — the constructor permits zero, Digest provides a reachable retry, and no code filters authentication responses from the count.

Divergence: **L3:** With `max_redirects=0`, authentication fails with `TooManyRedirects` despite following zero redirects. Expected: the authenticated request proceeds; observed by source trace: the second transport call never occurs.

Trigger: Configure `Client(max_redirects=0, auth=DigestAuth("u", "p"))`. Have the first response return 401 with `WWW-Authenticate: Digest realm="r", nonce="n", qop="auth"`; an authenticated retry would return 200. The client instead raises before that retry. AsyncClient behaves identically.

Remedy: In both redirect handlers, replace the limit condition with:

```python
if sum(r.has_redirect_location for r in history) > self.max_redirects:
```

Dry-run: The 401 contributes zero; authentication proceeds. A followed redirect still contributes one, so a zero allowance still blocks its destination request.

Verification: ⚠️ Unverified by execution — static trace only; runtime integration tests excluded by request.

### 🟡 Warning
**[L4] — An authentication retry erases preceding redirect history**

Premises: Redirect handling extends its local history using `history = history + [response]`, leaving the caller’s list unchanged. The returned response contains the accumulated history. Documentation promises followed redirects in `response.history` (`docs/quickstart.md:442`); auth-history tests separately require intermediate authentication responses.

Trace: [1] Starting with `history=[]`, a 302 followed by a 401 produces a returned 401 whose history is `[302]` (`_client.py:985–991`). [2] If authentication yields another request, [line 955 overwrites that history](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L955) with the outer, still-empty list. [3] Line 958 appends only the 401. [4] A successful retry consequently receives history `[401]`. Async lines 1702–1705 perform the same overwrite. Rebuttal check: PASSED — both response categories belong in history, this sequence is permitted by `Auth`, and no later code reconstructs the lost redirect.

Divergence: **L4:** Expected final history `[302, 401]`; source-derived actual history `[401]`. The 401’s own history is also incorrectly emptied, removing evidence of the followed redirect.

Trigger: Use an auth flow that yields the initial request, then yields `response.request` after a 401. Return `/start → 302 Location: /protected`; the first `/protected` request returns 401, and its retry returns 200. Enable `follow_redirects=True`.

Remedy: Replace `response.history = list(history)` at lines 955 and 1702 with:

```python
history = list(response.history)
```

Keep the subsequent `history.append(response)`.

Dry-run: The returned `[302]` is retained, then extended to `[302, 401]`; the successful response receives both entries. Auth-only and redirect-only paths preserve their existing ordering.

Verification: ⚠️ Unverified by execution — static trace only; runtime integration tests excluded by request.

### 🟡 Warning
**[L6] — Sending a directly constructed request omits the client timeout configuration**

Premises: `Request(...)` initializes absent extensions to `{}` (`_models.py:335`). Timeout configuration reaches transports through request extensions (`docs/advanced/extensions.md:10`). Client documentation states its configured timeout supplies the default for requests.

Trace: [1] `Request("GET", url)` has no `"timeout"` extension. [2] [Client.send](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L907) proceeds through auth and redirect handling without adding one; AsyncClient does likewise at line 1654. [3] `_send_single_request` passes this request to the transport. [4] The default transport forwards `request.extensions` unchanged to `httpcore` (`_transports/default.py:232`, async line 372). Rebuttal check: PASSED for the missing configuration — directly constructed requests are explicitly supported. Although `send` documents sending requests “as-is,” the documented default timeout has no other propagation path in the inspected code.

Divergence: **L6:** Expected: the configured client timeout reaches the transport when no request override exists. Source-derived actual: none of its timeout values reach the transport. The precise resulting backend timeout behavior remains unverified.

Trigger: Create `Client(timeout=0.1)` and send `Request("GET", "https://example.org/")`. At the transport handoff, `request.extensions` lacks `"timeout"`. In contrast, `client.build_request(...)` supplies all four values through `_client.py:352–358`.

Remedy: Immediately before authentication setup in both `send` methods, add:

```python
if "timeout" not in request.extensions:
    request.extensions["timeout"] = self.timeout.as_dict()
```

Dry-run: Bare requests receive the configured defaults; existing timeout extensions, including explicit disabled-timeout values, remain intact. Requests created with `build_request` retain their settings.

Verification: ⚠️ Unverified by execution — transport metadata omission established statically; backend behavior not exercised.

## Summary

The redirect limit can reject valid authentication, and authentication retries can discard redirect history. These are distinct from the timeout handoff defect.

**Open lead:** Whether missing timeout metadata causes indefinite waiting depends on backend behavior outside the inspected workspace; that consequence is not claimed as confirmed. Seven read-only tool calls were used, with no file modifications, external access, history inspection, or runtime tests.