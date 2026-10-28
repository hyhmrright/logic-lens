<!-- run a2e90991ee8349a996367f85d394431a; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/exceptions.py`, with targeted supporting reads of compatibility imports, callers, tests, and documentation.  
**Logic Score:** 93/100

> One concrete serialization defect identified by static tracing. Runtime behavior and the proposed remedy were not executed.

## Findings

### 🟡 Warning

**[L1] — Inherited pickle reducer cannot reconstruct `JSONDecodeError`**

Premises: [exceptions.py:31](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/exceptions.py#L31) inherits from `InvalidJSONError` before `CompatJSONDecodeError`. The first inheritance path reaches `IOError` (`OSError` on supported Python versions). The compatibility class is selected from `json` or `simplejson` in `compat.py:30–42`. Its constructor requires JSON-specific reconstruction arguments, including `msg`, `doc`, and `pos`.

Trace: [1] `JSONDecodeError("Expecting value", "", 0)` enters the constructor at `exceptions.py:34`. [2] Line 41 initializes the JSON exception, preserving its JSON attributes and setting `args` to the formatted message tuple. [3] Line 42 forwards that one-message tuple to `RequestException`, which initializes `OSError` at line 24. [4] When pickled, method resolution selects `OSError.__reduce__` before the JSON class’s specialized reducer; no override exists in the reviewed class. [5] Reconstruction calls the Requests exception constructor with the single formatted message. Line 41 then forwards that single argument to the JSON constructor, which requires the document and position too. Production reachability of the exception itself is established by `Response.json()`, which constructs it at `models.py:966` and `973`. Rebuttal check: PASSED — no constructor fallback or serialization override was found. Existing JSON tests check inheritance, message contents, and `doc`, but do not exercise exception pickling.

Divergence: **L1:** the inherited reducer resolves through the `OSError` branch rather than the JSON branch. **Expected:** a pickle round trip reconstructs the exception and its JSON details. **Statically predicted actual consequence:** deserialization raises `TypeError` for missing `doc` and `pos`, replacing the original decoding error with a reconstruction failure. This can prevent transporting the exception through serialization-based boundaries. No runtime failure was observed during this review.

Trigger: With the standard-library JSON backend selected, this minimal sequence exposes the mismatch:

```python
import pickle
from requests.exceptions import JSONDecodeError

error = JSONDecodeError("Expecting value", "", 0)
restored = pickle.loads(pickle.dumps(error))
assert (restored.msg, restored.doc, restored.pos) == (
    error.msg, error.doc, error.pos
)
```

Remedy: Add this method inside `JSONDecodeError` to select the backend’s reconstruction contract explicitly:

```python
    def __reduce__(self):
        return CompatJSONDecodeError.__reduce__(self)
```

Dry-run: The JSON reducer supplies the constructor arguments; reconstruction initializes the JSON attributes before the existing `RequestException` initialization. The trigger’s constructor mismatch is eliminated, and ordinary construction and catching remain unchanged. This is a mental verification only.

Verification: ⚠️ Unverified — no runtime reproducer, remedy execution, or integration tests were run under this read-only discovery protocol.

## Summary

The concrete defect is the exception’s incompatible inherited serialization behavior. Ordinary JSON-error construction preserves the message and JSON attributes; the failure occurs during reconstruction.

Open lead: whether an application actually serializes these exceptions, and what surrounding process or task framework does afterward, is not established by the supplied evidence. No additional concrete defects were found in the reviewed file. No files were modified or external services accessed.