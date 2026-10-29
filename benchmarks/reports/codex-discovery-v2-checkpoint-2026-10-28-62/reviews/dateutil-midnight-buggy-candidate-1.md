<!-- run 9ae6d9c643694ef29b9f904df83a730d; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `dateutil/parser/isoparser.py`; supporting parser tests, property test, public exports, and documentation. Nine shell calls used. No files modified.  
**Logic Score:** 86/100 — measures confirmed findings in the inspected paths, not overall correctness.

Two defects were reproduced on the local implementation.

## Findings

### 🟡 Warning — [L9] `24:00` loses the required day rollover

**Premises:** The public contract promises a datetime representing the ISO-8601 string and explicitly supports hour `24` (`isoparser.py:62–95,118–120`). In ISO notation, a date’s `24:00` denotes the following date’s `00:00`.

**Trace:**

1. `isoparse('2014-04-11T24:00')` parses date components `[2014, 4, 11]`.
2. `_parse_isotime()` parses hour `24` and minute `0`.
3. At [isoparser.py:367](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L367), it validates the remaining components and replaces hour `24` with `0`, discarding the rollover information.
4. `isoparse()` constructs `datetime(2014, 4, 11, 0, 0)` at line 142. No date adjustment follows.

Rebuttal check: `test_datetime_midnight` explicitly expects the same-day result (`test_isoparser.py:141–154`). That test preserves the implementation’s behavior but contradicts the documented ISO semantics; it masks this defect.

**Divergence:** **L9:** Normalizing the hour without advancing the calendar date returns a datetime one day earlier than the represented instant.

**Trigger:** `isoparse('2014-04-11T24:00')`

- Expected: `2014-04-12 00:00:00`.
- Observed: `2014-04-11 00:00:00`.

Likewise, `2014-12-31T24:00Z` incorrectly remains in 2014.

**Remedy:** Immediately after line 138’s `_parse_isotime()` call, insert:

```python
                if dt_str[pos + 1:pos + 3] == b'24':
                    return datetime(*components) + timedelta(days=1)
```

This preserves the time-only API’s normalization and the existing rejection of nonzero components after hour `24`. Dry-run: the in-memory replacement passed ordinary, leap-day, year-boundary, ordinal-date, week-date, offset, and stream checks.

**Verification:** Execution-verified on actual local source under Python 3.11.18. The remedy was executed separately in an in-memory copy. The existing midnight test would need its expected dates corrected.

### 🟡 Warning — [L2] Byte separators crash during construction on Python 3

**Premises:** [test_isoparser.py:294](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L294) explicitly exercises `sep=b'T'` and requires the resulting parser to round-trip a datetime. Its Python 3 `xfail` records the known failure.

**Trace:**

1. `isoparser(sep=b'T')` enters `__init__()` with a one-byte ASCII separator.
2. At [isoparser.py:51](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L51), both `len(sep) != 1` and `ord(sep) >= 128` evaluate false.
3. Evaluation reaches `sep in '0123456789'`, comparing `bytes` against a text string.
4. Python raises `TypeError` before `_sep` is assigned or parsing begins.

Rebuttal check: the `_takes_ascii` decorator only wraps parsing methods; it cannot normalize constructor arguments.

**Divergence:** **L2:** The constructor applies text operations to the supported byte representation, preventing parser construction.

**Trigger:**

```python
isoparser(sep=b'T').isoparse('2017-12-06T12:30:45')
```

Expected: `datetime(2017, 12, 6, 12, 30, 45)`.  
Observed: `TypeError: 'in <string>' requires string as left operand, not bytes`. Using `sep='T'` succeeds.

**Remedy:** Inside `if sep is not None:`, before the existing validation, insert:

```python
            if isinstance(sep, six.binary_type):
                sep = sep.decode('ascii')
```

Dry-run: the in-memory replacement accepted text and byte separators and retained rejection of empty, numeric, multicharacter, and non-ASCII separators.

**Verification:** Execution-verified on actual local source under Python 3.11.18; remedy verified in memory. Python 2 compatibility was not executed.

## Summary

The main defect silently shifts end-of-day timestamps backward by one day. The second prevents construction with byte separators on Python 3. The two proposed changes passed 30 combined in-memory checks covering the triggers and neighboring behavior.

Verification used local source without mocks, dependency installation, external services, or filesystem writes. The full test suite and historical Python versions were not run; these checks establish the exercised scenarios only.

## Unresolved Investigations

- **U1 — Compact year-month contract conflict:** `isoparser.py:75` advertises `YYYYMM`, but `test_isoparser.py:239` explicitly requires rejection. Execution confirmed that `201204` raises `ValueError`, whereas `2012-04` succeeds. Whether compact input is intended support or a documentation error remains unresolved; it is excluded from findings and scoring.
- **U2 — Numeric separator ambiguity with ordinal dates:** Default configuration promises any single separator. `2017011T123000` yields January 11 at 12:30, while replacing `T` with `0` yields January 10 at 23:00. The common-date route consumes the separator as a day digit. Potential impact is silent misinterpretation; the missing contract is precedence between ambiguous date representations. The next check is to establish that precedence before selecting a remedy.