<!-- run 42c2a2ea846e4727942e02bc08335ec9; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, focusing on year-day conversion/application and weekday equality/hashing. Supporting evidence: `_common.py`, local documentation, and relevant tests. Other arithmetic paths received limited inspection.  
**Logic Score:** 86/100

> Two concrete defects were reproduced on the actual local implementation.

## Findings

### 🟡 Warning — [L3] Day 366 resolves to December 30 in leap years

**Premises:** The documented `yearday` contract sets the absolute day within the given year; leap years count February 29. See [docs/relativedelta.rst:193](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/docs/relativedelta.rst#L193) and its leap-year example at line 212. Consequently, day 366 of 2024 is December 31.

**Trace:**

1. In [`__init__`:213](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L213), `yearday=366` sets `self.leapdays=-1`.
2. The conversion table maps this to `month=12, day=32`: `366 - 334 = 32`.
3. During addition, lines 377–378 clamp day 32 to December 31.
4. Lines 385–392 then subtract one day because December is after February and 2024 is a leap year, returning December 30.

Rebuttal check: month-end clamping does cover the invalid intermediate day, but its interaction with the subsequent leap correction causes the error.

**Divergence:** **L3 — Boundary Blindspot.** The final valid leap-year day receives both clamping and subtraction, placing it one day early.

**Trigger:**

```python
date(2024, 1, 1) + relativedelta(yearday=366)
# Expected: date(2024, 12, 31)
# Observed: date(2024, 12, 30)
```

**Remedy:** At line 213, replace:

```python
if yearday > 59:
```

with:

```python
if 59 < yearday < 366:
```

Dry-run: day 366 then clamps to December 31 without subtraction; day 365 retains its required leap correction.

**Verification:** Reproduced on actual source under Python 3.11.18. An in-memory source variant containing this remedy passed 4,386 assertions covering every valid year-day in 1900, 2000, 2023, and 2024, using both `date` and `datetime` inputs.

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup

**Premises:** The public weekday contract equates an unspecified occurrence with `+1` (class documentation, lines 53–56). `relativedelta.__eq__` additionally treats occurrence `0` as equivalent. Hashable equal objects must have equal hashes; dictionary use is explicitly exercised by [testHashable:647](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/tests/test_relativedelta.py#L647).

**Trace:**

1. Construct `a=relativedelta(weekday=MO)` and `b=relativedelta(weekday=MO(1))`. Their occurrence values are `None` and `1`.
2. Lines 523–529 consider those weekday representations equivalent; all remaining fields match, so `a == b` returns `True`.
3. [`relativedelta.__hash__`:547](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L547) hashes the original weekday object.
4. [`weekday.__hash__`:27](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/_common.py#L27) hashes `(weekday, n)` without canonicalizing `n`. The resulting delta hashes differ, and lookup using the equal delta misses.

Rebuttal check: applying either delta uses `n or 1` at line 394, confirming their equivalent weekday behavior. Neither hash function performs that normalization.

**Divergence:** **L6 — Callee Contract Mismatch.** Delegating directly to the weekday’s hash preserves distinctions that `relativedelta` equality deliberately removes. Equivalent keys can occupy separate set entries or fail dictionary lookup.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                       # True
{a: "found"}.get(b, "MISSING") # Observed: "MISSING"; expected: "found"
len({a, b})                   # Observed: 2; expected: 1
```

The same failure reproduced for `MO(0)` versus `MO(1)`.

**Remedy:** Replace `self.weekday,` at line 549 with:

```python
((self.weekday.weekday, self.weekday.n or 1)
 if self.weekday else None),
```

Dry-run: unspecified, zero, and first occurrences hash identically; distinct weekdays and other occurrence numbers retain their distinctions.

**Verification:** Reproduced on actual source. The in-memory remedy passed 77 equal-pair checks across all seven weekdays and occurrence values `None`, `0`, `1`, `-1`, and `2`, checking hashes, dictionary retrieval, and set deduplication.

## Summary

Both findings have complete traces and executed reproductions. The proposed remedies were tested together in memory; 14 neighboring application controls also passed. No files were modified, dependencies installed, or external services accessed.

Verification used the supplied Python interpreter with `PYTHONDONTWRITEBYTECODE=1` and local `src` on `PYTHONPATH`. The full test suite and other Python versions were not exercised. The score describes confirmed findings within this inspected slice.

## Unresolved Investigations

**U1 — Fractional days applied to `date`.** `date(2024,1,1) + relativedelta(days=1.5)` returns January 2 as a `date`; applying its normalized form returns January 2 at noon as a `datetime`. Both preserve noon when starting from a `datetime`. The missing fact is whether normalization promises identical behavior for plain-date inputs despite Python’s date/timedelta truncation semantics. This remains a lead, with no score deduction; the next check is an explicit contract or caller requirement for that case.