<!-- run d94c55e60b0c441ea7e9468bfb26b3d9; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `dateutil/parser/isoparser.py`, public exports, parser documentation, example tests, and the ISO round-trip property test. Focused on time parsing, midnight handling, separators, and date-format boundaries; not exhaustive.  
**Logic Score:** 79/100

Three behavioral defects reproduced. Two are already recorded as expected failures in the supplied tests. The score reflects confirmed findings in this inspected slice, not whole-project correctness.

## Findings

### 🟡 Warning — [L4] Midnight normalization is discarded

**Premises:** `_parse_isotime` accepts hour 24 when all smaller components are zero. `parse_isotime` explicitly normalizes that hour to zero before returning a `datetime.time`, whose valid hours are 0–23.

**Trace:**

1. `parse_isotime("24:00")` receives `[24, 0, 0, 0, None]` from `_parse_isotime`.
2. Lines 177–178 change the local list’s hour to `0`.
3. [Line 179](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L179) calls `_parse_isotime` again, producing a fresh list with hour `24`, and passes it to `datetime.time`.

Rebuttal check: the internal midnight guard permits this input; it only rejects nonzero minutes, seconds, or microseconds.

**Divergence:** **L4** — the return expression discards the normalized state. Supported midnight input raises `ValueError: hour must be in 0..23` instead of returning `datetime.time(0, 0)`.

**Trigger:** `isoparser().parse_isotime("24:00")`. Bytes, fractional-zero forms, and timezone-bearing forms also fail.

**Remedy:** Replace line 179 with:

```python
return time(*components)
```

Dry-run: the in-memory replacement passed 30 midnight cases covering text, bytes, fractions, and offsets. Stream inputs also passed; `24:00:01` remained rejected.

**Verification:** Reproduced on the actual implementation under Python 3.11.18. Remedy verified using an in-memory modified module.

### 🟡 Warning — [L2] Byte separators raise an incidental Python 3 exception

**Premises:** The supplied [`test_isoparser_byte_sep`](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L295) expects `sep=b"T"` to work and marks its Python 3 failure with `xfail`. The constructor validates and stores the separator.

**Trace:**

1. `isoparser(sep=b"T")` enters the non-`None` branch at line 50.
2. `len(sep) != 1` and `ord(sep) >= 128` are both false.
3. [Line 51](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L51) evaluates `sep in '0123456789'`: a bytes operand against a Unicode string.

Rebuttal check: conversion occurs only later, at line 55, so it cannot protect this operation.

**Divergence:** **L2** — Python 3 rejects that mixed-type membership test. Construction raises `TypeError` before any date can be parsed, contrary to the existing test’s expected behavior.

**Trigger:**

```python
isoparser(sep=b"T").isoparse("2017-12-06T12:30:45")
```

Expected: `datetime(2017, 12, 6, 12, 30, 45)`. Observed: `TypeError: 'in <string>' requires string as left operand, not bytes`.

**Remedy:** Inside `if sep is not None:`, before the existing validation, insert:

```python
if isinstance(sep, six.binary_type):
    sep = sep.decode('ascii')
```

Dry-run: text and byte separators for both `"T"` and space parsed their corresponding datetimes successfully.

**Verification:** Reproduced on the actual Python 3 implementation. In-memory remedy passed four constructor cases. Python 2 behavior was not executed.

### 🟡 Warning — [L3] Missing time separators are silently accepted

**Premises:** The supplied expected-failure tests explicitly require rejection of mixed formats: [`"20120425T01:2000"`](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L275) and `"14:3015"` at lines 475–483. This finding concerns that recorded rejection requirement; the documentation does not promise generally strict ISO validation.

**Trace:**

1. `_parse_isotime(b"14:3015")` sets `has_sep=True` because byte 2 is `:`.
2. It reads hour `14`, consumes the colon, and reads minute `30`.
3. At [lines 355–357](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L355), the next colon is optional. Its absence leaves the cursor unchanged.
4. The next iteration reads `15` as seconds, consumes the entire input, and returns normally.

Rebuttal check: the unused-component guard cannot reject this path because every character was consumed.

**Divergence:** **L3** — a required component boundary is not checked. Inputs the supplied tests designate as invalid produce successful parse results.

**Trigger:**

- `parse_isotime("14:3015")` returns `time(14, 30, 15)`; expected `ValueError`.
- `isoparse("20120425T01:2000")` returns `datetime(2012, 4, 25, 1, 20)`; expected `ValueError`.

**Remedy:** Replace lines 351–357 with:

```python
if comp < 3:
    # Hour, minute, second
    if comp > 0 and has_sep:
        if timestr[pos:pos + 1] != self._TIME_SEP:
            raise ValueError("Inconsistent use of colon separator")
        pos += 1
    components[comp] = int(timestr[pos:pos + 2])
    pos += 2
```

Dry-run: the modified parser rejected both mixed formats and neighboring malformed boundaries. Basic and colon-separated valid times continued to pass the exercised controls.

**Verification:** Both triggers reproduced on the actual implementation. The combined in-memory remedies passed 162 ordinary time controls spanning fractions and offsets, plus targeted midnight and rejection checks.

## Summary

The midnight finding prevents valid time-only inputs from parsing. The separator findings reproduce two issues already acknowledged by local expected-failure tests.

Verification used the supplied interpreter, local source, `six 1.17.0`, and a 10-second probe timeout with `PYTHONDONTWRITEBYTECODE=1`. Eight shell invocations were used, including one blocked heredoc attempt that was retried without temporary files. No files were modified or dependencies installed. The full suite and Python 2 were not run; remedy checks covered bounded scenarios.

## Unresolved Investigations

- **Compact year-month contract:** The docstring advertises `YYYYMM`, but `test_iso_raises` explicitly rejects `"201204"`. The actual parser rejects it. The workspace evidence does not establish which contract should prevail; reconcile those requirements before changing behavior.
- **Datetime-midnight test conflict:** `test_datetime_midnight` expects `"2014-04-11T24:00"` to remain on April 11, while `isoparse` returns April 12 through its explicit rollover branch. This discrepancy is separate from the confirmed time-only defect. The intended calendar-date expectation needs resolution before treating rollover as faulty.