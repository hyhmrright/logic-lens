<!-- run 71d41d00664f437e9b0fdb6c206434c0; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/exceptions.py`, supported by exception callers, compatibility imports, documentation, and relevant tests. Five read-only tool calls; no files modified or external services accessed.  
**Logic Score:** 93/100

One concrete serialization defect was identified through static analysis.

## Findings

### 🟡 Warning — **[L6] JSONDecodeError cannot be unpickled**

**Premises:** The wrapper inherits from both `InvalidJSONError` and the selected JSON decoder exception. The supplied `HISTORY.md:123–126` explicitly promises backward compatibility with previously thrown JSON exceptions. For the supported standard-library JSON backend (`compat.py:36–42`), serialization must retain the constructor’s `msg`, `doc`, and `pos` arguments.

**Trace:**

1. Invalid response JSON reaches either wrapper-raising branch in [models.py:965](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/models.py#L965), passing the decoder’s `msg`, `doc`, and `pos`.
2. [exceptions.py:41](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/exceptions.py#L41) initializes the decoder exception, then initializes `InvalidJSONError` using `self.args`: one formatted message.
3. The inheritance order places `RequestException` and `IOError` (`OSError` on Python 3) before the decoder exception. Consequently, serialization selects `OSError.__reduce__`, which supplies that single message as the reconstruction arguments.
4. Unpickling invokes the wrapper constructor with one argument. Its call to `CompatJSONDecodeError.__init__` requires three, so reconstruction raises `TypeError` before saved attributes can be restored.

**Rebuttal check:** No class in the target overrides `__reduce__` to select the decoder’s reconstruction arguments. Existing JSON tests (`tests/test_requests.py:2785–2797`) check inheritance, message formatting, and `doc`; they do not cover serialization.

**Divergence:** **L6 — Callee Contract Mismatch.** The inherited reducer’s reconstruction arguments do not satisfy the wrapper constructor. Expected: a JSON decoding exception survives a pickle round trip. Actual consequence under standard CPython behavior: loading fails with `TypeError` for missing `doc` and `pos`, preventing recovery of the original exception.

**Trigger:** With the standard-library JSON backend:

```python
import pickle
from requests.exceptions import JSONDecodeError

error = JSONDecodeError("Expecting value", "", 0)
restored = pickle.loads(pickle.dumps(error))
```

This also applies to exceptions caught from `Response.json()`. The trigger is provided for reproduction; it was **not executed**.

**Remedy:** Add this method to `JSONDecodeError`, delegating reconstruction arguments to the selected decoder while preserving instance attributes:

```python
def __reduce__(self):
    constructor, args = CompatJSONDecodeError.__reduce__(self)
    return constructor, args, self.__dict__
```

**Dry-run:** For the standard-library backend, reconstruction receives all three required arguments, then restores saved attributes. Ordinary exception construction remains unchanged. This remedy was checked mentally, not executed.

**Verification:** ⚠️ **Static evidence only.** Runtime integration tests were excluded by the requested discovery protocol. Neither the reproduction nor the remedy was executed. Optional `simplejson` implementation details were unavailable within the supplied workspace.

## Summary

The confirmed defect concerns JSON exception serialization; ordinary JSON exception construction and catch compatibility follow the inspected callers and tests. The base initializer also correctly handles falsey HTTP error responses by checking `response is not None`.

No additional concrete defects or open leads were established. The score measures confirmed findings within the inspected paths, not whole-project correctness.