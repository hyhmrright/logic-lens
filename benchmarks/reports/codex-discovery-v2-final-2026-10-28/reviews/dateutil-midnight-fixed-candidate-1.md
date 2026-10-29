<!-- run 1f9184777d414300ad25fa1a18299ee7; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `dateutil/parser/isoparser.py`, supported by parser exports, tests, documentation, and timezone implementations. Focused review within seven tool calls; not exhaustive.  
**Logic Score:** 86/100

Two behavioral defects were reproduced. The score reflects confirmed findings within the inspected paths.

## Findings

### 🟡 Warning

**[L4] — Standalone time parsing discards midnight normalization**

**Premises:** The parser explicitly supports hour 24 when the remaining components are zero ([isoparser.py:93](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L93)). `parse_isotime()` returns a `datetime.time`, so this representation must become hour 0.

**Trace:**

1. For `'24:00'`, `_parse_isotime()` returns `[24, 0, 0, 0, None]`; its midnight validation accepts these values.
2. `parse_isotime()` changes that list’s hour to 0 at line 178.
3. Line 179 calls `_parse_isotime(timestr)` again, producing a fresh list containing hour 24, and passes it to `datetime.time`.

Rebuttal check: the shared helper validates midnight but deliberately leaves normalization to its caller. No later normalization protects this constructor call.

**Divergence:** At [isoparser.py:179](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L179), the normalized state is discarded—an **L4** violation. Supported midnight inputs raise `ValueError: hour must be in 0..23`.

**Trigger:** `isoparser().parse_isotime('24:00')`. Expected: `datetime.time(0, 0)`. Observed: the exception above. `'24'`, fractional-zero midnight, bytes, streams, UTC, and fixed-offset variants also fail.

**Remedy:** Replace line 179 with:

```python
return time(*components)
```

Dry-run: an in-memory source variant passed all 28 midnight cases that failed against the original, plus invalid-midnight rejection and ordinary-time controls.

**Verification:** Execution-verified against the actual local implementation on Python 3.11.18. The remedy was executed only in memory.

### 🟡 Warning

**[L2] — A bytes separator crashes the constructor on Python 3**

**Premises:** The repository includes a bytes-separator test expecting `sep=b'T'` to parse successfully. It explicitly marks the Python 3 failure as expected ([test_isoparser.py:294](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L294)). This is an existing acknowledged failure.

**Trace:**

1. `isoparser(sep=b'T')` enters the non-`None` separator branch.
2. `len(sep) == 1` and `ord(sep) == 84`, so validation reaches its membership expression.
3. At line 51, `sep in '0123456789'` applies a bytes operand to a text container, raising `TypeError` before a parser is constructed.

Rebuttal check: `_takes_ascii` decorates parsing methods, so it cannot normalize the constructor argument.

**Divergence:** [isoparser.py:51](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L51) violates the bytes/text type boundary—**L2**. The intended equivalent separator representation prevents parsing entirely.

**Trigger:**

```python
isoparser(sep=b'T').isoparse('2017-12-06T12:30:45')
```

Expected: `datetime(2017, 12, 6, 12, 30, 45)`, matching `sep='T'`. Observed: `TypeError: 'in <string>' requires string as left operand, not bytes`.

**Remedy:** Inside `if sep is not None:`, before existing validation, insert:

```python
if isinstance(sep, six.binary_type):
    sep = sep.decode('ascii')
```

Dry-run: an in-memory variant passed six text/bytes separator cases, rejected six invalid separators, and continued rejecting mismatched date/time separators.

**Verification:** Execution-verified on the actual local implementation under Python 3.11.18; the text separator control succeeded. Historical Python versions were not exercised.

## Summary

Use the already-normalized components in `parse_isotime()` and normalize bytes separators before constructor validation. Both minimal remedies passed focused in-memory checks.

Probes used the supplied interpreter, `PYTHONDONTWRITEBYTECODE=1`, repository-root `PYTHONPATH`, and 10-second alarms. No files were changed, dependencies installed, or external services used. The complete test suite and historical runtimes were not tested.

## Unresolved Investigations

**U1 — Compact year-month contract conflict.** The public docstring lists `YYYYMM` as supported, but `test_iso_raises` explicitly requires `'201204'` to fail, and date-only fixtures support only `%Y-%m`. The implementation raises `ValueError`. The workspace does not resolve which contract should govern; confirm that before changing behavior.

**U2 — Datetime-midnight expectation conflict.** `test_datetime_midnight` expects `2014-04-11T24:00` to remain April 11, whereas the implementation returns April 12. This concerns datetime rollover, separately from finding 1’s standalone-time exception. Resolve the conflicting expectation before treating either the test or rollover behavior as defective.