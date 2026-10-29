<!-- run d014cbf393704ad39f121fcc4b659043; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `isoparser.py`, its public exports, parser tests, property test, documentation, and timezone offset implementation. Focus: date dispatch, time parsing, midnight, and separator handling. Eight tool calls used; no files modified.  
**Logic Score:** 72/100

Four behavioral defects reproduced. Two separator defects are already acknowledged by expected-failure tests.

## Findings

### 🟡 Warning

**[L6] — Compact ordinal dates can silently become different dates**

Premises: The ordinal-date tests support both `YYYYDDD` and `YYYY-DDD`; the parser constructor documents acceptance of any single separator by default. Thus `2017123 1230` represents May 3, 2017, at 12:30.

Trace:

1. [`_parse_isodate()`](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L200) tries the common calendar parser first.
2. That parser reads year `2017`, month `12`, and passes `b'3 '` to `int()` at line 244. Python accepts the trailing space, producing day `3`.
3. It returns position `8`, having consumed the intended separator. `isoparse()` then skips the first hour digit as though it were the separator and parses `230` as 23:00.
4. Rebuttal check: no exception occurs, so the ordinal fallback never runs. The equivalent extended representation parses correctly.

Divergence: **L6** — the common-date parser reports successful consumption of an ordinal date plus separator, preventing the caller’s format fallback and returning a different date and time.

Trigger:

```text
isoparse("2017123 1230")
Expected: 2017-05-03 12:30
Observed: 2017-12-03 23:00
```

`"2017123 12:30"` instead raises `ValueError`; `"2017-123 12:30"` succeeds.

Remedy: Replace the day conversion at line 244 with:

```python
daystr = dt_str[pos:pos + 2]
if not daystr.isdigit():
    raise ValueError('Invalid common day')
components[2] = int(daystr)
```

Dry-run: this rejects the common interpretation and activates the existing ordinal parser.

Verification: Reproduced on the actual implementation. The in-memory remedy corrected both compact-time and colon-time cases, including an explicitly configured space separator.

### 🟡 Warning

**[L9] — `24:00` loses the required calendar rollover**

Premises: The public API promises a datetime representing an ISO-8601 string and explicitly supports `24:00`. In that notation, the time denotes midnight ending the stated date.

Trace:

1. [`_parse_isotime()`](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L367) validates that all smaller components are zero.
2. Line 371 replaces hour `24` with `0`, discarding the distinction between the two midnights.
3. `isoparse()` constructs `datetime(*components)` with the original date.
4. Rebuttal check: no caller adds a day. The existing [midnight test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L141) explicitly expects the same-date result; it codifies behavior conflicting with the API’s ISO-8601 contract.

Divergence: **L9** — normalization loses the calendar-day carry, returning an instant 24 hours early.

Trigger:

```text
isoparse("2014-12-31T24:00+05:30")
Expected: 2015-01-01 00:00+05:30
Observed: 2014-12-31 00:00+05:30
```

Remedy: Delete line 371’s normalization. Immediately before `isoparse()` returns its datetime, insert:

```python
if len(components) > 3 and components[3] == 24:
    components[3] = 0
    return datetime(*components) + timedelta(days=1)
```

Replace `parse_isotime()`’s return statement with:

```python
components = self._parse_isotime(timestr)
if components[0] == 24:
    components[0] = 0
return time(*components)
```

Dry-run: datetime parsing preserves the day carry; time-only parsing continues returning midnight.

Verification: Reproduced on actual code against ISO midnight semantics. The in-memory remedy passed year-end and timezone-aware leap-day rollover checks and retained rejection of nonzero components after hour 24. The conflicting existing test would require correction.

### 🟡 Warning

**[L2] — A byte separator raises `TypeError` on Python 3**

Premises: The [existing byte-separator test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L294) expects `sep=b'T'` to parse successfully and marks its Python 3 failure explicitly.

Trace:

1. [`isoparser.__init__()`](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L50) receives `bytes`.
2. Length and `ord()` checks succeed.
3. `sep in '0123456789'` compares a byte operand against a text container, raising `TypeError`.
4. Rebuttal check: the input-normalization decorator wraps parsing methods, so it cannot protect constructor arguments.

Divergence: **L2** — validation mixes text and byte representations, preventing construction.

Trigger: `isoparser(sep=b'T')` should construct a parser equivalent to `isoparser(sep='T')`; observed result is `TypeError`.

Remedy: Insert before line 50:

```python
if isinstance(sep, six.binary_type):
    sep = sep.decode('ascii')
```

Dry-run: validation receives text, and the existing final encoding produces the internal byte separator.

Verification: Reproduced on actual code under Python 3.11.18. The in-memory remedy passed the existing test’s construction and datetime round trip.

### 🟡 Warning

**[L3] — Extended times accept a missing internal colon**

Premises: The [datetime test](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L275) and time-only test at line 475 explicitly require rejection of mixed separator forms. Both are marked as expected failures.

Trace:

1. [`_parse_isotime()`](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/parser/isoparser.py#L333) recognizes `14:3015` as extended format.
2. It consumes `14` and the following colon.
3. After consuming minute `30`, the optional-colon branch sees digit `1` and continues anyway.
4. It consumes seconds `15` and returns successfully. Rebuttal check: neither public wrapper performs additional separator validation.

Divergence: **L3** — the minute-to-second boundary does not enforce the selected extended format.

Trigger: `parse_isotime("14:3015")` should raise `ValueError`; observed result is `time(14, 30, 15)`. `isoparse("20120425T01:2000")` similarly succeeds.

Remedy: Replace lines 344–350 with:

```python
if comp < 3:
    if has_sep and comp > 0:
        if timestr[pos:pos + 1] != self._TIME_SEP:
            raise ValueError('Inconsistent time separators')
        pos += 1
    components[comp] = int(timestr[pos:pos + 2])
    pos += 2
```

Dry-run: each subsequent extended-format component requires its colon; timezone detection still precedes this branch.

Verification: Both failures reproduced on actual code. The in-memory remedy rejected both malformed forms.

## Summary

The highest-impact finding is silent corruption of compact ordinal datetimes; midnight normalization also returns the wrong calendar day. The score covers confirmed findings in this inspected slice, not whole-project correctness.

Verification used the local implementation with Python 3.11.18, bytecode disabled, and 10-second probe limits. Combined remedies were tested only in an in-memory source copy: all reproduced triggers passed, alongside 630 comparisons with original normal-path results. No full test suite, Python 2 run, external service, installation, or file write was performed. One initial shell heredoc attempt was blocked before Python execution.

## Unresolved Investigations

- **Compact year/month contract:** line 75 advertises `YYYYMM`, but the test at line 239 explicitly requires rejection. `"201204"` raises `ValueError`. No supplied caller resolves whether documentation or acceptance should change.
- **Numeric separators with compact ordinal dates:** the default separator contract permits digits, but `"2017123412:30"` is consumed as a common date and fails. The ordinal remedy above does not resolve this fully numeric ambiguity; format-disambiguation policy needs further investigation.