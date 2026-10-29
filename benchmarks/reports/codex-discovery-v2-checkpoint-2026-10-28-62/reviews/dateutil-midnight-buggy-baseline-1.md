<!-- run 51b8ee7f9d5544acafa3d23f342fedd0; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `dateutil/parser/isoparser.py`, its public exports, parser tests, property test, documentation, and relevant timezone behavior. Targeted date dispatch, midnight, and separator traces; malformed-input acceptance was not exhaustively reviewed.  
**Logic Score:** 79/100

Three confirmed defects: silent datetime corruption, a one-day midnight error, and rejection of a tested separator type. The score describes confirmed findings in this inspected slice.

## Findings

### 🟡 Warning — [L6] Basic ordinal dates with whitespace can produce incorrect datetimes

**Premises:** Ordinal-date support is established by [test_isoparser.py:195](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L195). The constructor documents acceptance of any single date/time separator by default. Thus `2017123 1234` represents ordinal day 123 of 2017—May 3—at 12:34.

**Trace:**

1. `_parse_isodate` tries `_parse_isodate_common` first.
2. At [isoparser.py:227](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L227), the common parser reads `12` as the month. At line 244, it passes `b'3 '` to Python’s `int`, which accepts the whitespace and returns `3`.
3. The common parser returns `[2017, 12, 3]` with position `8`; no exception invokes the ordinal fallback.
4. At [isoparser.py:138](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L138), `pos + 1` skips the first time digit. `_parse_isotime` receives `b'234'`, producing 23:04.

Rebuttal check: the permissive default separator and final `datetime` constructor both accept this path.

**Divergence:** **L6:** the common parser relies on `int` rejecting a field containing a separator. Its actual permissiveness causes both the date and time to change silently.

**Trigger:** `isoparse('2017123 1234')`

- Expected: `datetime(2017, 5, 3, 12, 34)`
- Observed: `datetime(2017, 12, 3, 23, 4)`

Other inputs, such as `'2017001 12:30:00'`, raise `ValueError` instead of parsing.

**Remedy:** Immediately before line 244, insert:

```python
        if not dt_str[pos:pos + 2].isdigit():
            raise ValueError('Invalid common day')
```

This lets the existing fallback parse the ordinal date. Dry-run: the in-memory replacement corrected both demonstrated cases.

**Verification:** Reproduced on the actual implementation under Python 3.11.18. Combined in-memory remedies passed the controls described below.

### 🟡 Warning — [L9] End-of-day midnight returns a datetime one day early

**Premises:** The module promises ISO-8601 parsing and explicitly supports `24:00`. In that notation, `2014-12-31T24:00Z` denotes the end of December 31, equivalent to `2015-01-01T00:00Z`.

**Trace:**

1. `isoparse` parses the date as `[2014, 12, 31]`.
2. `_parse_isotime` obtains hour `24` with zero smaller components.
3. At [isoparser.py:367](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L367), it validates the zeros and replaces hour `24` with `0`.
4. At [isoparser.py:142](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L142), `datetime(*components)` uses the original date.

Rebuttal check: [test_isoparser.py:141](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L141) explicitly expects same-day midnight. That test preserves the observed behavior but conflicts with the advertised ISO end-of-day semantics; it needs correction alongside the implementation.

**Divergence:** **L9:** normalization discards the day rollover, making the represented instant 24 hours early.

**Trigger:** `isoparse('2014-12-31T24:00Z')`

- Expected: `2015-01-01 00:00:00+00:00`
- Observed: `2014-12-31 00:00:00+00:00`

**Remedy:** Replace line 142 with:

```python
        result = datetime(*components)
        if len(dt_str) > pos and dt_str[pos + 1:pos + 3] == b'24':
            result += timedelta(days=1)
        return result
```

Dry-run: the in-memory replacement corrected year-end and leap-day rollover while preserving ordinary `00:00` and standalone time parsing.

**Verification:** Reproduced on the actual implementation. Calendar-boundary remedy checks passed in memory.

### 🟡 Warning — [L2] A bytes separator raises `TypeError` on Python 3

**Premises:** [test_isoparser.py:295](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L295) explicitly exercises `sep=b'T'` and expects successful parsing. It is already marked as an expected failure on Python 3.

**Trace:**

1. `isoparser(sep=b'T')` enters constructor validation.
2. `len(sep) == 1` and `ord(sep) < 128`, so evaluation reaches the membership check.
3. At [isoparser.py:51](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L51), `sep in '0123456789'` compares a `bytes` operand against a text string and raises `TypeError`.

Rebuttal check: construction has no bytes normalization before this expression; parsing is never reached.

**Divergence:** **L2:** separator validation mixes binary and text types, preventing the explicitly tested configuration from being constructed.

**Trigger:**

```python
isoparser(sep=b'T').isoparse('2017-12-06T12:30:45')
```

Expected: the corresponding datetime. Observed: `TypeError: 'in <string>' requires string as left operand, not bytes`.

**Remedy:** Inside `if sep is not None:`, before validation, insert:

```python
            if isinstance(sep, six.binary_type):
                sep = sep.decode('ascii')
```

Dry-run: the in-memory replacement returned the expected datetime.

**Verification:** Reproduced on Python 3.11.18; the proposed normalization passed the reproduced case.

## Summary

Prioritize ordinal-date dispatch because it can silently return a substantially different datetime. The midnight issue also silently changes the represented instant; bytes separators fail immediately.

Verification used the actual local implementation, `PYTHONDONTWRITEBYTECODE=1`, and a 10-second alarm for the final probe. Combined remedies were compiled only in memory: all three triggers passed, along with 1,440 date/time/separator/offset controls and additional midnight checks. The original implementation failed 120 of those controls, all involving basic ordinal dates with whitespace. No files were changed, dependencies installed, external services accessed, or full test suite run; Python 2 behavior remains unverified.

## Unresolved Investigations

- **U1 — Compact year-month contract conflict:** [isoparser.py:75](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L75) advertises `YYYYMM`, but [test_isoparser.py:239](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L239) explicitly requires rejection. The probe confirmed `'201704'` raises `ValueError`. Whether this is incorrect documentation or missing functionality needs a contract decision; it is not counted as a defect.