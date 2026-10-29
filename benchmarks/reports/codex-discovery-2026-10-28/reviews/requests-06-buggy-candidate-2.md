<!-- run ee59f7590186484fa9c2193d62bfcd7b; model gpt-6.1-sol; only temporary source links normalized -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/requests/exceptions.py`, supported by exception callers in `models.py`, `adapters.py`, and `sessions.py`; compatibility imports, documentation, and relevant tests. Five shell calls used. No files modified, external services accessed, or runtime tests executed.  
**Logic Score:** 93/100

One serialization defect is supported by static analysis. The score describes confirmed findings in the inspected paths, not whole-project correctness.

## Findings

### 🟡 Warning

**[L6] — `JSONDecodeError` cannot be reconstructed from its inherited pickle representation**

**Premises:** The public wrapper inherits both `RequestException` and the selected JSON decoder’s exception at [exceptions.py:31](https://github.com/psf/requests/blob/96b22fa18c00831656ee4b286bf1c9062459b00a/src/requests/exceptions.py#L31). The standard-library backend is explicitly supported by `compat.py:30–42`. Its decoding exception requires `(msg, doc, pos)` for construction. The wrapper’s constructor preserves that interface, while ordinary Python exception serialization must provide enough arguments to reconstruct the exception.

**Trace:**

1. With the standard-library backend selected, an empty response reaches `Response.json()` at `models.py:969`. Parsing raises the decoder’s exception.
2. `models.py:973` constructs the Requests wrapper using `e.msg`, `e.doc`, and `e.pos`.
3. `exceptions.py:41–42` initializes the decoder exception, then initializes `InvalidJSONError` using `self.args`. Those arguments contain one formatted message, such as `"Expecting value: line 1 column 1 (char 0)"`.
4. The inheritance order places `RequestException → IOError/OSError` before the decoder exception. Consequently, pickle uses `OSError.__reduce__`, which supplies the single message argument for reconstruction.
5. Unpickling invokes the wrapper with that single argument. Its call to `CompatJSONDecodeError.__init__` at line 41 lacks `doc` and `pos` and raises `TypeError`.

Rebuttal check: Neither the wrapper nor its Requests ancestors overrides the reducer. Existing JSON tests check exception membership, message contents, and `.doc`; they do not test serialization (`tests/test_requests.py:2785–2797`).

**Divergence:** **L6 — Callee Contract Mismatch.** The inherited reducer supplies arguments incompatible with the subclass constructor. Expected: serialization restores the decoding exception and its diagnostic fields. Actual consequence, derived statically: deserialization raises `TypeError` instead of returning the original exception.

**Trigger:** With `simplejson` absent:

```python
import pickle
from requests.exceptions import JSONDecodeError

error = JSONDecodeError("Expecting value", "", 0)
restored = pickle.loads(pickle.dumps(error))
```

The expected result is another `JSONDecodeError` with the same `msg`, `doc`, and `pos`. Reconstruction instead fails because `doc` and `pos` are missing.

**Remedy:** Add this method to `JSONDecodeError`, selecting the decoder’s constructor arguments and retaining Requests instance attributes:

```python
    def __reduce__(self):
        constructor, args = CompatJSONDecodeError.__reduce__(self)[:2]
        return constructor, args, self.__dict__
```

Dry-run: For the standard-library backend, reconstruction receives all three required arguments; restoring the instance dictionary retains `request` and `response`. Ordinary construction and exception matching are unaffected. This remedy was checked mentally, not executed.

**Verification:** ⚠️ **Unverified at runtime — static evidence only.** Runtime integration tests were excluded by the requested protocol. The predicted failure uses Python’s standard exception-reduction behavior; no installed dependency implementations were read. The optional `simplejson` backend was not independently verified.

## Summary

The actionable defect is the mismatch between `JSONDecodeError`’s constructor and its inherited serialization behavior. Request/response attachment and the inspected exception inheritance paths yielded no additional confirmed defects.

No open leads are being promoted to findings; optional-backend and executed remedy validation remain outside this review’s coverage.