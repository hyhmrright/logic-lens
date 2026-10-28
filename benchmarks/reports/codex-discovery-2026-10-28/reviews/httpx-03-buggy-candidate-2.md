<!-- run 9f4100f9e57747c4a1213673e17bef28; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `httpx/_client.py`, focusing on transport selection, authentication, redirects, and timeout propagation. Supporting evidence: transport implementations, request models, authentication classes, related tests and documentation. Seven read-only shell calls; no files changed, external services accessed, or runtime tests run. This was a targeted review, not exhaustive coverage.  
**Logic Score:** 86/100

> Two confirmed defects in the inspected paths; one timeout question remains unresolved.

## Findings

### 🟡 Warning

**[L6] — Environment proxies override the async application shortcut**

**Premises:** `AsyncClient` documents `app` as an application to receive requests instead of making network requests (`httpx/_client.py:1359`). The shortcut remains supported despite its deprecation warning. With an application supplied and no explicit proxy or transport, requests should reach that application.

**Trace:**

1. At [httpx/_client.py:1430](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430), `allow_env_proxies = trust_env and transport is None` evaluates to `True` with default arguments, even when `app` is supplied.
2. `_get_proxy_map()` imports environment proxies, and the constructor creates corresponding network transport mounts.
3. `_init_transport()` independently creates `ASGITransport(app=app)` at line 1479.
4. `_transport_for_url()` selects a matching proxy mount before falling back to that ASGI transport. `_send_single_request()` dispatches through the selected network transport.

Rebuttal check: the synchronous constructor explicitly excludes `app` from environment proxy selection. The async constructor lacks that defense. Explicit `transport=` or `trust_env=False` avoids this path.

**Divergence:** L6: configuring an in-process application does not guarantee dispatch to it. A matching environment proxy causes the application to receive no request and causes an outbound network attempt instead.

**Trigger:** Supply `HTTP_PROXY=http://127.0.0.1:9999`, with no matching `NO_PROXY` exclusion, then use `AsyncClient(app=hello_world)` to GET `http://testserver/`. Expected: invoke `hello_world`. Actual by static trace: dispatch through the HTTP proxy; the eventual response or connection error depends on that proxy.

**Remedy:** Replace line 1430 with:

```python
allow_env_proxies = trust_env and app is None and transport is None
```

Dry-run, static only: application-backed clients bypass automatic proxy mounts; ordinary clients retain environment proxy behavior.

**Verification:** Unverified at runtime—runtime integration tests were excluded by the review protocol. The dispatch divergence is supported by the complete source path.

### 🟡 Warning

**[L4] — Authentication retries discard preceding redirect history**

**Premises:** `docs/quickstart.md:442` promises that response history contains followed redirects in order. `tests/client/test_auth.py:658–707` establishes that intermediate authentication responses also appear in history. Custom multi-request authentication flows are explicitly supported by `Auth.auth_flow()`.

**Trace:**

1. `_send_handling_auth()` passes its initial empty `history` list to redirect handling.
2. For `/start → 302 /protected → 401`, redirect handling rebinds its local history using `history = history + [response]` (`httpx/_client.py:991`). The returned 401 therefore has `[302]` in its history, while the authentication handler’s list remains empty.
3. If authentication yields another request, [httpx/_client.py:955](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L955) overwrites that 401’s history with the empty outer list, then appends only the 401.
4. A successful retry directly to `/protected` consequently returns history `[401]`. Async handling repeats the same operations at lines 1702–1705 and 1739.

Rebuttal check: existing tests exercise redirects and authentication histories separately. Neither response reading nor the subsequent dispatch restores the discarded redirect.

**Divergence:** L4: separate history lists lose previously recorded state. Both clients omit an actual followed redirect from the final response and erase it from the intermediate authentication response.

**Trigger:** With `follow_redirects=True`, use an authentication flow that first yields `/start`, receives the redirected 401, adds an authorization header to `response.request`, and yields that `/protected` request again. Let the retry return 200. Expected final history: `[302, 401]`; actual by static trace: `[401]`.

**Remedy:** In both authentication handlers, replace:

```python
response.history = list(history)
```

with:

```python
history = list(response.history)
```

Keep the subsequent `history.append(response)`.

Dry-run, static only: the trigger retains `[302, 401]`; authentication without redirects and requests without authentication retries retain their existing history sequences.

**Verification:** Unverified at runtime—runtime integration tests were excluded. Both synchronous and asynchronous source paths establish the same loss.

## Summary

The confirmed defects affect application routing and response history. The proposed edits are minimal but have only been checked by static tracing. The score reflects confirmed findings in this inspected slice, not whole-project correctness or shipping readiness.

## Unresolved Investigations

**U1 — Client timeouts on directly constructed requests.** `Request(...)` initializes empty extensions (`httpx/_models.py:335`), and both `send()` implementations forward these without inserting the client timeout. The default transports pass those extensions directly to `httpcore`.

This appears inconsistent with the “timeout everywhere” contract in `docs/advanced/timeouts.md:1–4,32–37`, while `send()` also documents sending requests “as-is.” The downstream implementation is outside the supplied workspace. Thus, the confirmed observation is missing timeout propagation; an indefinite wait has **not** been established. Next check: resolve the direct-send timeout contract and verify downstream behavior in an authorized runtime review. This lead does not reduce the score.