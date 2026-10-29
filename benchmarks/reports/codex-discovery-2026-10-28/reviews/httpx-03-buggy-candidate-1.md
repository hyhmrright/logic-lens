<!-- run ff841c2718d8469fa0106024e6c86cb9; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** Targeted traces of `httpx/_client.py`: transport selection, authentication retries, redirect history, and explicit-request timeout propagation. Supporting evidence came from workspace models, transports, utilities, documentation, and tests. Used 8/10 tool calls; this was not an exhaustive review.  
**Logic Score:** 86/100

Two defects are confirmed by static traces. Runtime reproduction and remedy verification were excluded by the requested protocol.

## Findings

### 🟡 Warning — [L6] Environment proxies bypass the configured ASGI application

**Premises:** `CHANGELOG.md:608` explicitly states that supplying `app=...` or `transport=...` bypasses environment proxy defaults. `_transports/asgi.py:48–65` describes the app shortcut as calling the application directly. The shortcut remains supported, with a deprecation warning.

**Trace:**

1. In [AsyncClient initialization](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L1430), `app` is supplied, `transport=None`, and default `trust_env=True`. Nevertheless, `allow_env_proxies` evaluates to `True`.
2. `_get_proxy_map()` obtains environment proxy mappings. For a hypothetical `HTTP_PROXY=http://127.0.0.1:9999` with no bypass, `_utils.py:205–210` produces an `http://` proxy mapping.
3. `_init_transport()` creates the intended `ASGITransport`, but initialization also creates an `AsyncHTTPTransport` proxy mount.
4. `_transport_for_url()` at lines 1515–1517 selects that matching mount. `_send_single_request()` invokes its network handler instead of the ASGI handler.

Rebuttal check: `trust_env=False`, an applicable `NO_PROXY` entry, or explicit `transport=ASGITransport(...)` avoids this path. None protects the default app-shortcut configuration. The synchronous constructor already includes the missing `app is None` condition at line 684.

**Divergence:** **L6:** automatic proxy selection violates the app shortcut’s direct-dispatch contract. The application receives no request; execution enters the network proxy transport instead. The resulting response or connection error depends on the proxy.

**Trigger:** With the hypothetical proxy configuration above, construct `AsyncClient(app=app, base_url="http://testserver")` and request `/`. Expected: call `app`. Actual source-derived behavior: dispatch through the HTTP proxy transport.

**Remedy:** Replace line 1430 with:

```python
allow_env_proxies = trust_env and app is None and transport is None
```

Dry-run: the app shortcut stops creating automatic proxy mounts; ordinary network clients retain environment proxy support. Explicit proxy arguments remain supported.

**Verification:** Static evidence only. Neither environment values nor external services were accessed. The remedy was mentally traced, not executed.

### 🟡 Warning — [L4] Authentication retries erase followed redirects from history

**Premises:** `docs/quickstart.md:442–444` promises that response history contains followed redirects in order. `tests/client/test_auth.py:658–707` additionally establishes that intermediate authentication responses belong in history. `_auth.py:38–58` supports authentication flows that yield additional requests.

**Trace:**

1. An authentication flow sends `/start`. It receives a `302` redirect to `/protected`, followed by a `401` response.
2. `_send_handling_redirects()` rebinds its local `history` using `history + [response]` at line 991. The returned `401` therefore has `history=[302]`, while the authentication handler’s original list remains empty.
3. The authentication flow yields a retry of `/protected`.
4. In [the authentication handler](https://github.com/encode/httpx/blob/df5345140e09ac6c2de0d9589bcd6f3e31c6aa3f/httpx/_client.py#L955), `response.history = list(history)` replaces `[302]` with `[]`. The handler then appends only the `401`.
5. A successful retry returns `200` with `history=[401]`. The followed `302` has disappeared.

Rebuttal check: ordinary redirects retain history when authentication finishes immediately. Existing authentication-history tests exercise retries without redirects. The async implementation repeats the faulty overwrite at line 1702.

**Divergence:** **L4:** the overwrite discards history already accumulated by the redirect handler. Expected final history is `[302, 401]`; actual history is `[401]`. The intermediate `401.history` is also incorrectly emptied.

**Trigger:** Use either client with `follow_redirects=True`, a custom `Auth` that retries `response.request` once, and a transport returning `/start → 302 /protected`, then `/protected → 401`, then retry `/protected → 200`.

**Remedy:** At both lines 955 and 1702, replace:

```python
response.history = list(history)
```

with:

```python
history = list(response.history)
```

Dry-run: the handler preserves the redirect chain before appending the authentication response. With no redirects, it retains the existing authentication-history behavior.

**Verification:** Static evidence only. No reproduction or modified-copy test was executed.

## Summary

Fix the ASGI routing condition first because it can send intended in-process requests into a network transport. Then preserve accumulated redirect history across authentication retries. The score reflects only these two confirmed warnings in the inspected slice; it does not establish whole-file correctness.

## Unresolved Investigations

**U1 — Explicit `Request` objects omit client timeout configuration.** Potential impact: network operations exceeding the configured client timeout.

`Request` initializes `extensions={}` at `_models.py:335`. Both `send()` implementations bypass the timeout setup in `build_request()` at `_client.py:352–358`, and the default transports forward the empty extensions unchanged at `_transports/default.py:232` and `372`. This conflicts with the broad timeout guarantee in `docs/advanced/timeouts.md:1–4,32–38`, although `send()` also documents sending requests “as-is.”

The configured timeout’s omission is established. A resulting unbounded wait remains unconfirmed: the supplied workspace lacks `httpcore` implementation evidence for missing-timeout behavior, and runtime integration tests were excluded. The next discriminating check is a contract clarification and an authorized regression test comparing explicit `Request` dispatch with `build_request()` dispatch. This lead does not reduce the score.