<!-- run 5320f5dee3514040b01cf29c8fec40b5; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, with focused traces through construction, date addition, equality, and hashing. Supporting evidence: `_common.py`, relativedelta tests/documentation, and `NEWS`. Other arithmetic and timezone interactions were not exhaustively investigated.  
**Logic Score:** 86/100

Two confirmed defects were reproduced on the local implementation. This score describes confirmed findings within the inspected paths, not whole-project correctness.

## Findings

### 🟡 Warning — [L3] `yearday=366` selects December 30 in leap years

**Premises:** The documented `yearday` parameter sets the ordinal day within the resulting year (`relativedelta.py:66–68`; `docs/relativedelta.rst:186–220`). Existing tests distinguish leap-year ordinal dates from non-leap-year dates (`tests/test_relativedelta.py:170–179`). In 2020, ordinal day 366 is December 31.

**Trace:**

1. At `relativedelta.py:211–214`, `yearday=366` sets `self.leapdays = -1`.
2. At lines 216–224, the month table converts 366 to `month=12, day=32`.
3. During addition, lines 377–378 clamp December 32 to December 31.
4. Lines 385–392 then subtract one leap day, returning December 30.

Rebuttal check: the day clamp handles invalid month-day combinations, but here it discards the extra day before the leap adjustment. The neighboring input `yearday=365` correctly returns December 30; both inputs therefore produce the same date.

**Divergence:** **L3** — the upper valid ordinal-day boundary is mishandled. Applying `relativedelta(yearday=366)` in a leap year returns a date one day earlier than required.

**Trigger:**

```python
date(2020, 1, 1) + relativedelta(yearday=366)
# Expected: date(2020, 12, 31)
# Observed: date(2020, 12, 30)
```

**Remedy:** At `src/dateutil/relativedelta.py:214`, replace:

```python
self.leapdays = -1
```

with:

```python
self.leapdays = -1 if yearday < 366 else 0
```

Dry-run: the in-memory replacement returns December 31 for day 366 and preserves the ordinary leap adjustment for days 60–365.

**Verification:** Execution-verified on actual local source with Python 3.11.18. The in-memory remedy passed 5,846 checks covering all valid ordinal days across 1900, 2000, 2020, and 2021; multiple date/datetime starting values; and non-leap ordinal days. Nearby month-end, relative-day, absolute-year, and invalid-day controls also passed. These checks do not establish general regression freedom.

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup and set deduplication

**Premises:** The public contract explicitly makes an unspecified weekday occurrence equivalent to `+1` (`relativedelta.py:51–56`). `relativedelta.__eq__` also equates occurrence values `None`, `0`, and `1` (lines 528–530). Dictionary-key usage is supported by `tests/test_relativedelta.py:647–651`. Equal hashable objects must have equal hashes.

**Trace:**

1. Constructing `relativedelta(weekday=MO)` and `relativedelta(weekday=MO(1))` retains weekday objects whose `n` values are respectively `None` and `1`.
2. `relativedelta.__eq__`, lines 523–545, treats these deltas as equal.
3. `relativedelta.__hash__`, lines 547–565, hashes the original weekday object without applying that equivalence.
4. `_common.weekday.__hash__`, lines 27–31, hashes `(weekday, n)` directly. The resulting delta hashes differ, so dictionary lookup by the equal alternative misses.

Rebuttal check: date application already normalizes these occurrences using `self.weekday.n or 1` at line 394. That normalization does not protect hashing.

**Divergence:** **L6** — `relativedelta.__hash__` delegates to a weekday hash whose equality distinctions differ from its own. Equivalent deltas can occupy separate set entries and fail to retrieve an existing dictionary value.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                  # True
{a: "value"}.get(b)      # Expected: "value"; observed: None
len({a, b})             # Expected: 1; observed: 2
```

**Remedy:** Within `src/dateutil/relativedelta.py:547`, replace the hash tuple’s `self.weekday,` entry with:

```python
((self.weekday.weekday, self.weekday.n or 1)
 if self.weekday is not None else None),
```

Dry-run: this gives equivalent weekday occurrences the same hash representation while retaining distinct representations for other occurrences.

**Verification:** Execution-verified on actual local source for both `MO` versus `MO(1)` and `MO` versus `MO(0)`. The in-memory remedy passed 77 equality/hash/dictionary/set checks across all seven weekdays, with occurrences `None`, `0`, `1`, `2`, and `-1`.

## Summary

Both findings have concrete observable consequences: an incorrect ordinal date and failed lookup/deduplication for equal objects. Both proposed remedies were tested entirely in memory; no files were modified.

Verification used the supplied interpreter, local `src` on `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`, and a 10-second process alarm. No dependencies were installed, external services accessed, or full test suite run. An initial heredoc invocation was blocked by the read-only environment; the successful probe used `python -c`.

## Unresolved Investigations

**U1 — Fractional days behave differently before and after normalization when added to a `date`.** The actual implementation returned `date(2020, 1, 1)` for `date(2020, 1, 1) + relativedelta(days=0.5)`, but normalization first returned `datetime(2020, 1, 1, 12)`. `NEWS:686–688` supports fractional relative days, while the inspected fractional-addition tests use `datetime` inputs. The required promotion or truncation behavior for plain `date` inputs remains unestablished. Next check: establish that contract before classifying the observed precision loss as a defect. This lead does not affect the score.