<!-- run f09f94f05fe341a9bdbe2385f44b14fa; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `dateutil/parser/isoparser.py`, its public exports, parser tests, property test, and generated API documentation. Traced midnight normalization, separator handling, date representations, fractions, and offsets. Bounded review; no exhaustive malformed-input or concurrency testing.  
**Logic Score:** 86/100

> Two confirmed defects: midnight loses its date rollover, and byte separators crash on Python 3.

## Findings

### 🟡 Warning

**[L3] — `24:00` produces a datetime one day early**

**Premises:** The parser promises ISO-8601 datetime interpretation, including `24:00` ([documented contract](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L93)). ISO end-of-day notation means `2014-04-11T24:00` represents `2014-04-12T00:00`.

**Trace:**

1. `isoparse()` parses the date as `[2014, 4, 11]`.
2. `_parse_isotime(b'24:00')` produces hour `24`, with zero minutes, seconds, and microseconds.
3. The midnight branch resets the hour to `0`, discarding the rollover ([line 371](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L367)).
4. `isoparse()` constructs `datetime(*components)` using the unchanged date.

Rebuttal check: the [existing midnight test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L141) explicitly expects the same-day result. That test conflicts with the promised ISO interpretation and therefore masks the defect.

**Divergence:** **L3:** normalization crosses the hour boundary without advancing the calendar date. The returned datetime is one day early, including for supported fixed-offset timestamps.

**Trigger:**

```python
isoparse("2014-04-11T24:00")
# Expected: datetime(2014, 4, 12, 0, 0)
# Observed: datetime(2014, 4, 11, 0, 0)
```

It also makes `24:00` compare earlier than the preceding `23:59:59`; their observed difference is `-1 day, 0:00:01`.

**Remedy:** In `isoparser.py`, delete `components[0] = 0` from `_parse_isotime()`. Replace the final return in `isoparse()` with:

```python
if len(components) > 3 and components[3] == 24:
    components[3] = 0
    return datetime(*components) + timedelta(days=1)
return datetime(*components)
```

Preserve time-only normalization by replacing `parse_isotime()`’s return with:

```python
components = self._parse_isotime(timestr)
if components[0] == 24:
    components[0] = 0
return time(*components)
```

Change the midnight test assertion to:

```python
assert isoparse(dt_str) == datetime(
    2014, 4, 12 if 'T24' in dt_str else 11)
```

Dry-run: the in-memory remedy corrected ordinary, year-end, leap-day, ordinal-date, and week-date rollover cases while preserving time-only midnight behavior.

**Verification:** Reproduced on the actual local implementation under Python 3.11.18. All five rollover assertions failed on the original and passed on the in-memory modified copy.

### 🟡 Warning

**[L2] — Byte separators raise `TypeError` on Python 3**

**Premises:** The repository’s [byte-separator test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L294) requires `sep=b'T'` to parse the same datetime as `sep='T'`. It is marked as an expected failure specifically on Python 3.

**Trace:**

1. `isoparser(sep=b'T')` enters the constructor’s separator validation.
2. `len(sep) != 1` and `ord(sep) >= 128` both evaluate false.
3. At [line 51](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L50), `sep in '0123456789'` evaluates bytes membership against a text string.
4. Python 3 raises `TypeError`; construction stops before parsing.

Rebuttal check: datetime input normalization cannot protect this route because the exception occurs in the constructor.

**Divergence:** **L2:** separator validation mixes bytes and text. A supported byte representation crashes instead of behaving like its text equivalent.

**Trigger:**

```python
isoparser(sep=b'T').isoparse("2017-12-06T12:30:45")
# Expected: datetime(2017, 12, 6, 12, 30, 45)
# Observed: TypeError:
# 'in <string>' requires string as left operand, not bytes
```

**Remedy:** Inside `if sep is not None:`, before the existing validation, insert:

```python
if isinstance(sep, six.binary_type):
    sep = sep.decode('ascii')
```

Dry-run: the in-memory remedy accepted equivalent text/byte separators and retained rejection of numeric, multiple-character, and non-ASCII separators.

**Verification:** Reproduced on the actual implementation: `'T'` succeeded and `b'T'` failed. The same byte-separator assertion passed with the in-memory remedy.

## Summary

Fix the date rollover first because it silently changes timestamps; separator handling causes an immediate exception. Across both remedies, 49 nearby checks passed in memory.

Verification used local source, Python 3.11.18, `PYTHONDONTWRITEBYTECODE=1`, and 10-second probe limits. No files were changed, dependencies installed, or external services accessed. Python 2, other Python versions, and the full test suite were not exercised. The score describes confirmed findings in the inspected slice, not whole-project correctness.

## Unresolved Investigations

**U1 — Conflicting `YYYYMM` support claims.** The parser docstring lists `YYYYMM` as supported, but `test_iso_raises` explicitly labels it invalid. The actual call `isoparse("201204")` raises `ValueError`. If the documented format is required, this rejects supported input; if the rejection is intentional, the documentation is wrong. No independent workspace evidence resolved that conflict, so it is not counted as a confirmed behavioral defect. The next check is a format-contract decision between those two sources.