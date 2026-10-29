<!-- run cf06f96715874009934add9f66f1e063; model gpt-6.1-sol; source links normalized only -->

I reproduced four behavioral defects and two lower-priority compatibility/documentation issues. All findings below are verified; no unverified leads are presented.

1. **`24:00` produces a datetime one day early.**  
   `isoparse("2014-12-31T24:00Z")` returns `2014-12-31 00:00:00+00:00`. Expected: `2015-01-01 00:00:00+00:00`, because `24:00` denotes the end of the specified day.

   [_parse_isotime, line 367](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L367) replaces hour 24 with 0, losing the rollover information before `isoparse` constructs the datetime. The same error occurs with numeric offsets. The [midnight test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L141) explicitly expects the incorrect same-day result, so existing coverage preserves this bug.

2. **Time parsing accepts inconsistent separators and incomplete components.**  
   Observed:
   - `parse_isotime("14:3015")` → `14:30:15`
   - `parse_isotime("14:30:")` → `14:30:00`
   - `parse_isotime("123")` → `12:03:00`

   Expected: rejection of these malformed forms; supported components use two digits, with consistent separators. At [line 344](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L344), component slices need not contain two characters, and colons are consumed when present without being required. A trailing colon can therefore terminate parsing successfully.

   Consequence: malformed input silently becomes an ordinary time. The [expected-failure test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L275) explicitly identifies inconsistent separators as needing a fix.

3. **Week 53 is accepted in years that have only 52 ISO weeks.**  
   `parse_isodate("2014-W53-1")` returns `2014-12-29`. That date’s ISO calendar tuple is `(2015, 1, 1)`, so the result does not preserve the supplied ISO year/week. Expected: `ValueError`; Python’s `date.fromisocalendar(2014, 53, 1)` independently rejects it.

   [_calculate_weekdate, line 310](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L310) checks only that the week lies between 1 and 53, then adds weeks without checking whether week 53 exists in that year. Consequently, impossible week dates silently map into the following ISO year. Valid `2015-W53-1` parses correctly as a control.

4. **Timezone components accept embedded signs and negative minutes.**  
   Observed:
   - `parse_tzstr("+01:-1")` → UTC offset `+00:59`
   - `parse_tzstr("+-1")` → UTC offset `−01:00`
   - `parse_tzstr("+00-99")` → UTC offset `−01:39`

   Expected: `ValueError`; documented offsets have one leading sign followed by unsigned, fixed-width components.

   At [line 389](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L389), `int()` accepts signs inside component slices. Subsequent validation checks upper bounds only. These malformed offsets also pass through `isoparse`: `"2014-01-01T12:34:56+01:-1"` becomes a datetime with offset `+00:59`, silently assigning an unintended instant.

5. **A byte separator crashes on Python 3.**  
   `isoparser(sep=b"T")` raises `TypeError: 'in <string>' requires string as left operand, not bytes`; `sep="T"` works.

   The constructor’s [line 51](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L51) tests a byte separator for membership in a text string before normalizing its type. Expected byte-separator behavior is demonstrated by the existing [Python-3-specific expected-failure test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L294). This is a compatibility issue rather than incorrect datetime arithmetic.

6. **The documented `YYYYMM` format is deliberately rejected.**  
   The [supported-format list, line 75](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L75) promises `YYYY-MM` or `YYYYMM`. However, `isoparse("201204")` raises `ValueError: Invalid ordinal day`, while `"2012-04"` returns April 1.

   This is a confirmed documentation inconsistency: implementation and tests explicitly reject `YYYYMM`. The evidence supports correcting the advertised formats, rather than assuming the parser must accept this form.

The malformed-input findings concern validation behavior; the module explicitly warns that rejection strictness is not a stable contract.

Verification used the supplied Python 3.11 interpreter against the local implementation, with bytecode writing disabled. Targeted probes reproduced these findings, and 192 ordinary datetime round trips passed. I did not run the full test suite or verify other Python versions. No files were modified, dependencies installed, or external services accessed.