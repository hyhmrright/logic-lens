<!-- run a5b05f383c384c5ba8f96d7cba5662e3; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** [isoparser.py](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py), its public exports, local unit/property tests, parser documentation, and fixed-offset dependencies. Ten shell calls used; no files modified.  
**Logic Score:** 79/100

> Three concrete defects were reproduced. The score describes confirmed findings within the inspected paths, not overall correctness.

## Findings

### 🟡 Warning
**[L4] — Reparsing discards midnight normalization**

**Premises:** Hour 24 with zero lower components is explicitly supported at `isoparser.py:93–95,374–377`. `parse_isotime()` normalizes it to hour zero at lines 176–178, allowing representation as `datetime.time`.

**Trace:**

1. `parse_isotime("24:00")` calls `_parse_isotime()`, which returns `[24, 0, 0, 0, None]`.
2. Line 178 changes that list’s hour to zero.
3. Line 179 calls `_parse_isotime()` again instead of using the corrected list.
4. The fresh list still contains hour 24; `datetime.time` raises `ValueError`.

Rebuttal check: `_parse_isotime()` validates midnight but deliberately preserves hour 24. No later normalization covers the second result.

**Divergence:** **L4**, line 179: the normalized state is discarded. A supported midnight input raises instead of returning `time(0, 0)`.

**Trigger:** `isoparser().parse_isotime("24:00")` raises `ValueError: hour must be in 0..23`. The offset-bearing input `"24:00:00.000+05:30"` fails identically.

**Remedy:** Replace line 179 with:

```python
        return time(*components)
```

Dry-run: the in-memory replacement returned midnight successfully, including across 84 string, byte, stream, precision, and offset combinations.

**Verification:** Execution-verified against the actual local implementation on Python 3.11.18. Remedy verification was limited to the described probes.

### 🟡 Warning
**[L2] — Byte separators crash on Python 3**

**Premises:** `test_isoparser.py:294–302` explicitly exercises `sep=b"T"` and expects a successful datetime round trip. Its Python 3 expected-failure marker documents an existing unsupported path.

**Trace:**

1. `isoparser(sep=b"T")` enters the constructor.
2. At line 51, `len(sep) != 1` and `ord(sep) >= 128` both evaluate false.
3. Evaluation reaches `sep in '0123456789'`, mixing `bytes` with `str`.
4. Python raises `TypeError` before separator storage or datetime parsing.

Rebuttal check: `_takes_ascii` only decorates parsing methods; it cannot normalize constructor arguments.

**Divergence:** **L2**, line 51: valid byte separator configuration crashes during validation. Expected: the datetime round trip specified by the local test.

**Trigger:**

```python
isoparser(sep=b"T").isoparse("2017-12-06T12:30:45")
```

Observed: `TypeError: 'in <string>' requires string as left operand, not bytes`.

**Remedy:** Immediately inside `if sep is not None:`, before the existing validation, insert:

```python
            if isinstance(sep, bytes):
                sep = sep.decode('ascii')
```

Dry-run: the in-memory replacement passed the exact round-trip assertion.

**Verification:** Execution-verified on Python 3.11.18. Python 2 compatibility was not executed.

### 🟡 Warning
**[L3] — Extended time parsing permits missing colons**

**Premises:** The local tests explicitly require rejection of `"20120425T01:2000"` (`test_isoparser.py:275–283`) and `"14:3015"` (lines 475–483). Both are marked expected failures and identified as inconsistent separator use. This supplies a specific rejection requirement beyond the parser’s general strictness caveat.

**Trace:**

1. Parsing `"14:3015"` sets `has_sep=True` because position 2 contains `:`.
2. Lines 353–357 parse hour 14 and consume that colon.
3. The next iteration parses minute 30, but the optional-colon condition simply does nothing when the second colon is absent.
4. The following iteration parses second 15; all input is consumed, so the parser returns `time(14, 30, 15)`.

Rebuttal check: neither the unused-input check nor `datetime.time` validates separator consistency. The same helper serves `isoparse()`.

**Divergence:** **L3**, lines 355–357: a required component delimiter is treated as optional. Malformed input is silently accepted where the local tests require `ValueError`.

**Trigger:** `"14:3015"` returns `time(14, 30, 15)`; `"20120425T01:2000"` returns `datetime(2012, 4, 25, 1, 20)`.

**Remedy:** Replace lines 351–357 with:

```python
            if comp < 3:
                if comp > 0 and has_sep:
                    if timestr[pos:pos + 1] != self._TIME_SEP:
                        raise ValueError(
                            'Inconsistent use of colon separator')
                    pos += 1
                components[comp] = int(timestr[pos:pos + 2])
                pos += 2
```

Dry-run: consuming required colons before minutes/seconds rejects both triggers while preserving basic formats, reduced precision, and timezone boundaries. This final replacement was checked statically only.

**Verification:** Both defects were execution-verified on actual code. An initial in-memory remedy passed the primary trigger but failed a trailing-colon boundary assertion. The corrected remedy above was not executed: the final probe contained a harness syntax error.

## Summary

Prioritize the discarded midnight normalization and the constructor’s byte/string mismatch; both have small remedies that passed their primary in-memory checks. Separator validation also has explicit local evidence, but its final proposed fix needs execution verification.

Probes used the supplied Python interpreter, local source, `PYTHONDONTWRITEBYTECODE=1`, and 10-second alarms. No dependencies were installed and no service or integration tests ran. The full test suite was not executed; one initial shell heredoc was blocked before Python ran.

## Unresolved Investigations

- **Datetime midnight contract:** `isoparse("2014-04-11T24:00")` returns April 12, while `test_isoparser.py:141–154` expects April 11. The local evidence conflicts; this was not reported as a date-shift defect. Resolve the intended dated-midnight semantics before changing behavior.
- **Compact year/month contract:** The public docstring lists `YYYYMM`, but `test_isoparser.py:239` explicitly rejects it, and `"201204"` raises `ValueError`. Determine whether the advertised format or rejection test should change. This unresolved inconsistency does not reduce the score.