<!-- run 4f67173d3caf43638afe8c2f663ac5e0; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `dateutil/parser/isoparser.py`; supporting exports, documentation, parser tests, property test, and Python support configuration. Traced date/time assembly, midnight normalization, and separator validation. No history or external services accessed; no files modified.  
**Logic Score:** 86/100

Two confirmed defects: midnight loses its date rollover, and byte separators crash construction on Python 3. The score describes confirmed findings in the inspected paths, not whole-project correctness.

## Findings

### 🟡 Warning
**[L3] — `24:00` silently produces a timestamp one day early**

**Premises:** The public API promises ISO-8601 datetime parsing and explicitly supports `24:00` (`isoparser.py:62–68,93–95`). In that representation, `24:00` denotes the end of the specified day, equivalent to the following day’s `00:00`. The supplied input is an ASCII string with valid date and time components.

**Trace:**

1. `isoparse("2016-12-31T24:00Z")` parses the date into `[2016, 12, 31]` and calls `_parse_isotime`.
2. `_parse_isotime` reads hour `24` and UTC. At [isoparser.py:367](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L367), it verifies that the smaller time components are zero, then replaces hour `24` with `0`.
3. `isoparse` constructs `datetime(*components)` at line 142 without advancing the date.

Rebuttal check: no caller restores the rollover. The existing [midnight test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L141) explicitly expects same-day midnight for both `00` and `24`; that expectation conflicts with the API’s ISO-8601 contract and masks this defect.

**Divergence:** **L3**, at hour normalization and subsequent datetime construction: the date carry is discarded. Expected `2017-01-01 00:00:00+00:00`; observed `2016-12-31 00:00:00+00:00`. This silently changes the represented instant by 24 hours.

**Trigger:** `isoparse("2016-12-31T24:00Z")`. Ordinary dates and month boundaries are affected too.

**Remedy:** Immediately after line 138, inside the successful separator branch, insert:

```python
                if dt_str[pos + 1:pos + 3] == b'24':
                    return datetime(*components) + timedelta(days=1)
```

This preserves standalone `parse_isotime("24:00")` normalization. Dry-run: the in-memory change passed 112 rollover combinations covering calendar, ordinal, and week dates with several offsets; ordinary times and rejection of nonzero components after hour 24 also passed. The midnight test must separately expect the following day for its `24` cases.

**Verification:** ✅ Execution-verified against the actual local implementation. The original returned the wrong date; the proposed in-memory change passed the same assertion.

### 🟡 Warning
**[L2] — A byte separator crashes construction on Python 3**

**Premises:** The repository’s [byte-separator test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L294) explicitly expects `isoparser(sep=b'T')` to parse a datetime successfully. It marks the Python 3 failure as expected. Python 3 is supported by `setup.py:63,77–83`. Here, `sep` is a one-byte ASCII `bytes` object.

**Trace:**

1. `isoparser(sep=b'T')` enters `__init__`.
2. At [isoparser.py:51](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L51), `len(sep) != 1` and `ord(sep) >= 128` both evaluate false.
3. Validation evaluates `b'T' in '0123456789'`. Python 3 rejects a bytes operand in string membership, raising `TypeError` before the parser is constructed.

Rebuttal check: constructor input bypasses `_takes_ascii`; its conversion cannot protect this path. The existing expected-failure marker acknowledges the problem without correcting it.

**Divergence:** **L2**, at the numeric-character membership test: validation mixes `bytes` and `str`. Expected successful construction and parsing; observed `TypeError: 'in <string>' requires string as left operand, not bytes`.

**Trigger:**

```python
isoparser(sep=b'T').isoparse('2017-12-06T12:30:45')
```

Expected `datetime(2017, 12, 6, 12, 30, 45)`; construction fails first.

**Remedy:** Before the existing `if sep is not None:` in `__init__`, insert:

```python
        if isinstance(sep, six.binary_type):
            sep = sep.decode('ascii')
```

Dry-run: the in-memory change passed byte and text separator cases, preserved default behavior, and rejected numeric, multiple-character, and non-ASCII separators.

**Verification:** ✅ Execution-verified against the actual local constructor. The original raised the predicted `TypeError`; the proposed in-memory change passed the same parsing assertion.

## Summary

Prioritize the midnight rollover because it silently returns the wrong instant. Both defects reproduced using Python 3.11.18 with six 1.17.0 and the workspace implementation; remedies were evaluated only in memory. No full test suite or other Python versions were exercised.

## Unresolved Investigations

**U1 — Conflicting `YYYYMM` contract.** `isoparser.py:75` lists `YYYYMM` as supported, but `test_isoparser.py:239` explicitly requires rejection, and lines 349–350 identify only the dashed year-month format as supported. The actual call `isoparse("201204")` raises `ValueError("Invalid ordinal day")`; following the documentation would imply `2012-04-01`. The intended contract remains disputed. Resolve that documentation/test conflict before deciding whether to change parsing behavior. This lead is excluded from findings and scoring.