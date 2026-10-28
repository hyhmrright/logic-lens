<!-- run 1b5538419f244d7caa40ee4dc203b9f2; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens — Logic Review

**Mode:** Logic Review  
**Scope:** `dateutil/parser/isoparser.py`, supported by parser exports, unit/property tests, documentation, and timezone-offset code. Deep traces focused on midnight normalization, separator types, and time delimiters; remaining paths were not exhaustively exercised.  
**Logic Score:** 79/100

Three confirmed defects were reproduced. The score reflects confirmed findings within this scope, not whole-project correctness.

## Findings

### 🟡 Warning — [L4] Midnight normalization is discarded

**Premises:** The parser documents support for hour 24 as midnight (`isoparser.py:93–95`). `_parse_isotime` permits it only when minutes, seconds, and microseconds are zero (`374–377`). The public time parser explicitly converts 24 to 0.

**Trace:**

1. `parse_isotime("24:00")` calls `_parse_isotime`, receiving `[24, 0, 0, 0, None]`.
2. Lines 177–178 change that list’s hour to 0.
3. [Line 179](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L179) calls `_parse_isotime` again, producing a new list containing hour 24.
4. `datetime.time` rejects that hour. **Rebuttal check:** the helper’s midnight validation permits this exact input; the normalized list never reaches the constructor.

**Divergence:** **L4 — State Mutation Hazard.** Line 179 discards the normalization. Expected: `datetime.time(0, 0)`. Observed: `ValueError: hour must be in 0..23`. Zoned midnight inputs also fail.

**Trigger:** `isoparser().parse_isotime("24:00")`, also `"24:00:00.000Z"`.

**Remedy:** Replace line 179 with:

```python
return time(*components)
```

**Dry-run:** The in-memory replacement returned midnight for compact/extended forms, timezone suffixes, strings, bytes, and streams. Nonzero components after hour 24 remained rejected.

**Verification:** Reproduced against the actual local implementation on Python 3.11.18. Remedy verification used an in-memory source copy.

### 🟡 Warning — [L2] A bytes separator crashes construction on Python 3

**Premises:** `test_isoparser_byte_sep` (`test_isoparser.py:294–302`) explicitly expects `isoparser(sep=b"T")` to support a datetime round trip. It is already marked as an expected failure on Python 3.

**Trace:**

1. `isoparser(sep=b"T")` enters constructor validation.
2. `len(sep) != 1` and `ord(sep) >= 128` are both false.
3. [Line 51](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L51) evaluates `sep in '0123456789'`: its left operand is `bytes`, while the right operand is `str`.
4. Python raises `TypeError` before construction completes. **Rebuttal check:** the ASCII encoding at line 55 happens afterward and cannot prevent this failure.

**Divergence:** **L2 — Type Contract Breach.** Expected: construct the parser and return `datetime(2017, 12, 6, 12, 30, 45)` for the repository’s example. Observed: `TypeError: 'in <string>' requires string as left operand, not bytes`.

**Trigger:**

```python
isoparser(sep=b"T").isoparse("2017-12-06T12:30:45")
```

**Remedy:** Inside `if sep is not None:`, before the existing validation, insert:

```python
if isinstance(sep, six.binary_type):
    sep = sep.decode('ascii')
```

**Dry-run:** In-memory checks passed for text/bytes separators `T`, space, and `_`; invalid empty, numeric, multicharacter, and non-ASCII separators remained rejected.

**Verification:** Reproduced on the actual implementation. This is an existing expected-failure case, not a newly uncovered test scenario. Python 2 was not exercised.

### 🟡 Warning — [L3] Missing time delimiters are silently accepted

**Premises:** The supported formats distinguish `hhmmss` from `hh:mm:ss`. More directly, `test_isoparser.py:275–283` and `475–483` expect rejection of mixed forms such as `"01:2000"` and `"14:3015"`. These tests are marked as expected failures; the first explicitly identifies excess leniency needing correction.

**Trace:**

1. `_parse_isotime(b"14:3015")` sets `has_sep=True` because position 2 contains `:`.
2. It reads hour 14 and consumes that colon.
3. It reads minute 30. At [lines 355–357](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L355), the next character is not `:`, so optional delimiter consumption is skipped.
4. It reads the remaining `15` as seconds. All characters are consumed, yielding `time(14, 30, 15)`. **Rebuttal check:** the unused-components check cannot detect the missing delimiter because no input remains.

**Divergence:** **L3 — Boundary Blindspot.** The minute/second boundary does not enforce the selected extended format. Expected, per the explicit tests: `ValueError`. Observed: a successful parse. This concerns those stated rejection cases; it does not establish a general promise of strict validation.

**Trigger:** `isoparser().parse_isotime("14:3015")` or `isoparse("20120425T01:2000")`.

**Remedy:** Replace lines 353–357 with:

```python
if has_sep and comp > 0:
    if timestr[pos:pos + 1] != self._TIME_SEP:
        raise ValueError('Inconsistent use of colon separator')
    pos += 1
components[comp] = int(timestr[pos:pos + 2])
pos += 2
```

**Dry-run:** The in-memory replacement rejected both mixed forms and retained sampled supported basic/extended formats, fractional seconds, and offsets.

**Verification:** Both examples reproduced on actual code. Remedy checks used an in-memory source copy.

## Summary

The three remedies together passed **2,033 targeted assertions** in memory. Separately, **384 sampled datetime round trips** across all ASCII separators passed on the original implementation.

Probes used the authorized Python 3.11.18 interpreter, local source via `PYTHONPATH=.`, `PYTHONDONTWRITEBYTECODE=1`, and a 10-second alarm per probe. No files were modified or dependencies installed. Full pytest/Hypothesis suites, Python 2, services, and integration tests were not run; the targeted checks do not establish regression-free fixes.

## Unresolved Investigations

- **Compact year-month contract:** The docstring lists `YYYYMM` as supported (`isoparser.py:75`), but `test_isoparser.py:239` explicitly requires `"201204"` to fail. Actual behavior is `ValueError`. The conflicting evidence prevents classifying rejection as a defect; the missing fact is which contract governs.
- **Datetime midnight expectation:** `test_datetime_midnight` expects `"2014-04-11T24:00"` to remain April 11, while implementation returns April 12. This expectation conflicts with end-of-day midnight semantics. No datetime-rollover defect is claimed; the stale or intentional nature of that test remains unresolved.