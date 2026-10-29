<!-- run 3da47ce1797e475fa9bc1eccb765ae22; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/models.py`, with supporting traces through `sessions.py`, `adapters.py`, `utils.py`, `_types.py`, tests, and documentation. Deep coverage focused on body preparation, redirects, authentication, and line iteration. Eight tool calls; no files modified or runtime tests executed.  
**Logic Score:** 86/100

Three defects are supported by static traces. The score reflects confirmed findings in this slice, with deductions capped per L-code within the module.

## Findings

### 🟡 Warning — [L6] Seekable readers without iteration cannot replay their bodies on redirects

**Premises:** Non-iterable, seekable readers are supported inputs: `tests/test_requests.py:841` exercises a `TestStream` implementing `read`, `tell`, `seek`, and `__len__`, without `__iter__`. The body-preservation requirement for a seekable POST across a 307 redirect is demonstrated at `tests/test_requests.py:239`.

**Trace:**

1. With `TestStream("test")`, [prepare_body](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L599) takes the non-`Iterable` branch.
2. `_encode_params()` recognizes its `SupportsRead` interface and returns the reader unchanged. `super_len()` calculates four remaining bytes, so preparation sets `Content-Length: 4`.
3. Position recording exists only inside the `Iterable` branch. `_body_position` therefore remains `None`.
4. After the first transmission consumes the reader, `PreparedRequest.copy()` retains that same exhausted reader and `None` position.
5. On a 307 or 308, `Session.resolve_redirects()` preserves the body and headers, but its [rewind condition](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/sessions.py#L278) evaluates false. The next request retains an exhausted reader and `Content-Length: 4`.

Rebuttal check: the reader has a working `seek`; the failure is that Requests never records the position needed to invoke it. The inspected adapter contains no compensating rewind.

**Divergence:** **L6:** `prepare_body()` accepts the reader returned by `_encode_params()` but omits the replay metadata required by the redirect consumer. Expected: resend `b"test"`. Actual: the redirected request exposes an exhausted body while still advertising four bytes. A resulting peer timeout is possible but was not verified.

**Trigger:** Use the existing test’s `TestStream("test")` as POST data, consume it during the first transmission, then receive a same-host 307 or 308 redirect.

**Remedy:** Remove the position-recording block at `models.py:609–618`. Immediately after `self.body = body` at line 650, insert:

```python
        if getattr(body, "tell", None) is not None:
            try:
                self._body_position = body.tell()
            except OSError:
                self._body_position = object()
```

Dry-run: records the original offset for both iterable and non-iterable readers; bytes retain `None`. Partially consumed readers retain their starting offset.

**Verification:** ⚠️ Static evidence only. Redirect integration and remedy execution were outside the requested protocol.

### 🟡 Warning — [L3] CRLF crossing chunk boundaries creates an extra empty line

**Premises:** `iter_lines()` promises one item per response line (`models.py:996`). `iter_content()` permits arbitrary chunk boundaries and uses `iter_slices()` for cached content. A CRLF represents one line ending regardless of where chunks divide it.

**Trace:**

1. For cached content `b"a\r\nb\r\n"`, `iter_content(chunk_size=2)` produces `b"a\r"`, `b"\nb"`, and `b"\r\n"`.
2. [iter_lines()](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L1015) applies `splitlines()` to `b"a\r"`, yielding `b"a"` and retaining no pending state.
3. It splits the next chunk, `b"\nb"`, into `[b"", b"b"]`, yields the empty item, and retains `b"b"`.
4. The final chunk completes that pending line, yielding `b"b"`.

Rebuttal check: this uses one iterator and cached bytes, so neither network scheduling nor the documented non-reentrancy restriction explains the result.

**Divergence:** **L3:** splitting each chunk independently forgets that a trailing CR may pair with the next chunk’s LF. Expected output: `[b"a", b"b"]`. Actual statically determined output: `[b"a", b"", b"b"]`. Consumers receive a blank line absent from the response.

**Trigger:**

```python
r = requests.Response()
r._content = b"a\r\nb\r\n"
r._content_consumed = True
list(r.iter_lines(chunk_size=2))
```

**Remedy:** Add `skip_lf = False` before the loop. Insert this block immediately inside the loop, before the existing pending-content concatenation:

```python
            if not delimiter:
                if not chunk:
                    continue
                lf = "\n" if isinstance(chunk, str) else b"\n"
                cr = "\r" if isinstance(chunk, str) else b"\r"
                if skip_lf and chunk.startswith(lf):
                    chunk = chunk[1:]
                skip_lf = chunk.endswith(cr)
                if not chunk:
                    continue
```

Dry-run: suppresses the LF paired with the previous CR, preserves genuine additional blank lines, and leaves explicit-delimiter handling unchanged.

**Verification:** ⚠️ Static evidence only. The supplied input and remedy were traced manually, not executed.

### 🟡 Warning — [L3] Authentication that empties a body leaves its old Content-Length

**Premises:** Custom authentication callables may modify a request before dispatch (`docs/user/advanced.rst:493`). Requests promises to override `Content-Length` when content length is determinable (`docs/user/quickstart.rst:228`). `prepare_auth()` explicitly recomputes the length after invoking the callable.

**Trace:**

1. Preparing POST data `b"abc"` establishes `Content-Length: 3`.
2. An auth callable sets `r.body = b""` and returns `r`.
3. [prepare_auth()](https://github.com/psf/requests/blob/0b401c76b6e80a4eecf3c690085b2553f6e261ca/src/requests/models.py#L688) calls `prepare_content_length(b"")`.
4. `super_len(b"")` returns integer zero. At `models.py:656`, `if length` is false, leaving the existing header untouched.
5. `HTTPAdapter.send()` selects non-chunked transmission because `Content-Length` exists and passes the empty body with length three to `urlopen()`.

Rebuttal check: this is a known-length bytes object, not an unknown-length stream. The adapter does not recalculate its length.

**Divergence:** **L3:** the truthiness check excludes a valid zero length. Expected: `body == b""` and `Content-Length: 0`. Actual: `body == b""` and `Content-Length: 3`, producing inconsistent request framing.

**Trigger:**

```python
def empty_body(r):
    r.body = b""
    return r

requests.Request(
    "POST", "http://example.com/",
    data=b"abc", auth=empty_body,
).prepare()
```

**Remedy:** In `prepare_content_length()`, replace `if length:` at line 656 with:

```python
            if length or isinstance(body, (str, bytes)):
```

Dry-run: empty strings and bytes receive length zero; positive-length bodies retain existing behavior. Empty file streams remain excluded, preserving the chunked-body behavior asserted at `tests/test_requests.py:2210`.

**Verification:** ⚠️ Static evidence only. Neither framing behavior against a server nor the remedy was executed.

## Summary

The strongest cross-file defect is the missing replay position for supported non-iterable readers. The other findings produce extra response lines and stale request lengths at zero-length boundaries. All proposed remedies remain unexecuted; this review does not establish correctness of untraced paths.

## Unresolved Investigations

**URL port zero:** `prepare_url()` reconstructs the authority using `if port:` (`models.py:541`). If `parse_url()` returns integer `0` for an explicit `:0`, preparation would discard that port. The dependency implementation was unavailable within the permitted workspace evidence, so this remains an open lead. Next check: establish that parser behavior before reporting a defect.