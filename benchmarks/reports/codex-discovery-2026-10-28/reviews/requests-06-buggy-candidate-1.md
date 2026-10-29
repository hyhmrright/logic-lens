<!-- run b210fa988ecd438db7024c27347f1416; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/exceptions.py`, with targeted caller, compatibility, documentation, and test reads. Covered JSON exception construction/serialization, request/response attachment, and timeout inheritance. Five shell calls; no files modified or runtime tests executed.  
**Logic Score:** 93/100

One statically established serialization defect was found. The score describes confirmed findings in the inspected paths, not whole-project correctness.

## Findings

### 🟡 Warning

**[L6] — `JSONDecodeError` cannot be unpickled with the standard-library JSON backend**

**Premises:** When `simplejson` is absent, [compat.py:30](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/compat.py#L30) selects Python’s `json.JSONDecodeError`. That exception requires `(msg, doc, pos)` for reconstruction. The wrapper inherits it alongside `RequestException`, which inherits `IOError`/`OSError`. Compatibility with previously thrown JSON exceptions is explicitly stated in `HISTORY.md:123–126`; tests at `tests/test_requests.py:2785–2797` check backend compatibility and document preservation.

**Trace:**

1. Invalid response JSON reaches [models.py:969](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/models.py#L969), which catches the backend exception and constructs `RequestsJSONDecodeError(e.msg, e.doc, e.pos)`.
2. [exceptions.py:41](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/exceptions.py#L41) initializes the backend exception. Its `args` contains one formatted error message, while `msg`, `doc`, and `pos` are separate attributes.
3. Line 42 initializes the `InvalidJSONError`/`RequestException` branch using that single message.
4. Because `OSError` precedes the backend JSON exception in method resolution order, pickling selects `OSError.__reduce__`. It records the wrapper class and its single-message `args`.
5. Unpickling calls the wrapper with that single argument. Line 41 forwards it to the backend constructor, which raises `TypeError` because `doc` and `pos` are missing.

Rebuttal check: Neither exception branch defines a reducer that supplies the required constructor arguments. Restoring the saved attribute dictionary cannot help: construction fails before that state is restored. Existing JSON tests do not exercise serialization.

**Divergence:** **L6 — constructor/reconstruction contract mismatch.** Expected: a serializable JSON decoding exception round-trips with its type, message, document, and position intact. Statically derived behavior: deserialization raises `TypeError` instead. Persisting or transporting a caught JSON error therefore fails when it is reconstructed.

**Trigger:** With the standard-library JSON backend:

```python
import pickle
from requests.exceptions import JSONDecodeError

error = JSONDecodeError("Expecting value", "", 0)
restored = pickle.loads(pickle.dumps(error))
```

Expected: `restored` represents the same decoding failure. Derived actual result: `JSONDecodeError.__init__()` reports missing `doc` and `pos`. This also applies to exceptions produced by `Response.json()`.

**Remedy:** Add this method to `JSONDecodeError`:

```python
def __reduce__(self):
    return CompatJSONDecodeError.__reduce__(self)
```

Dry-run: the backend reducer supplies its constructor’s required fields instead of the single formatted message. Ordinary construction and catching remain unchanged. This remedy was checked mentally for the stated trigger, not executed.

**Verification:** ⚠️ **Static evidence only.** No reproduction or remedy test was run, as requested. The trace uses Python’s standard exception reduction semantics; runtime and dependency implementations outside the supplied workspace were not inspected.

## Summary

The confirmed defect prevents standard-backend JSON decoding exceptions from surviving a pickle round-trip. No additional defects were confirmed in the inspected request/response attachment or timeout inheritance paths.

## Unresolved Investigations

- **Optional `simplejson` backend:** Its selection is evidenced in `compat.py`, but its implementation is absent from the supplied workspace. Its precise reduction behavior and the proposed remedy’s behavior with that backend remain unverified. Next check: inspect the supported backend’s constructor and reducer, then validate reconstruction when runtime verification is authorized. This is an open scope limitation, not a second confirmed defect.