<!-- run 18566ec3f29a4b8ab5134cf3992b97cf; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, supported by its documentation, tests, `_common.weekday`, and the timezone caller. Focused traces covered ordinal dates, equality/hashing, date arithmetic, normalization, and date differences. This was a bounded review, not exhaustive path coverage.  
**Logic Score:** 86/100

Two confirmed defects were reproduced on the actual implementation. The score reflects confirmed findings within the inspected scope.

## Findings

### 🟡 Warning — [L3] `yearday=366` returns December 30 in leap years

**Premises:** The documented `yearday` contract selects the ordinal day within the given year ([documentation](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/docs/relativedelta.rst#L186)). Existing tests exercise this interpretation across leap and ordinary years. The 366th day of 2000 is December 31.

**Trace:**

1. Constructing `relativedelta(yearday=366)` sets `leapdays=-1` because the ordinal exceeds 59.
2. The constructor’s month table converts 366 into `month=12, day=32`.
3. During addition, `__add__` clamps day 32 to December 31, then applies the leap-year adjustment of −1 day.

Rebuttal check: Month-end clamping prevents an invalid date exception, but it does not preserve the requested ordinal.

**Divergence:** The conversion at [lines 213–224](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L213), followed by clamping and adjustment at lines 377–392, collapses ordinals 365 and 366 onto December 30 in leap years. This is an **L3 boundary blindspot**.

**Trigger:**

```python
date(2000, 1, 1) + relativedelta(yearday=366)
# Expected: date(2000, 12, 31)
# Observed: date(2000, 12, 30)
```

**Remedy:** Replace line 214 with:

```python
self.leapdays = -1 if yearday != 366 else 0
```

Dry-run: This preserves the existing December 31 clamp for ordinal 366 while avoiding the extra subtraction. The replacement passed the same probes in an in-memory copy.

**Verification:** Execution-verified on actual source under Python 3.11.18. Across 2,193 valid ordinal dates in six selected years, the original failed only on ordinal 366 in the three leap years; the in-memory remedy passed all cases. Month-end, non-leap ordinal, and date-difference controls also passed.

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup and set deduplication

**Premises:** The public weekday contract treats omitted `n` as `+1`. `relativedelta.__eq__` additionally equates `n=None`, `0`, and `1`. The class explicitly supports hashing, exercised by `testHashable` at `tests/test_relativedelta.py:647`. Equal hashable objects must have equal hashes.

**Trace:**

1. Construct `a=relativedelta(weekday=MO)` and `b=relativedelta(weekday=MO(1))`.
2. `relativedelta.__eq__` treats these weekday specifications as equivalent and returns `True`.
3. `relativedelta.__hash__` hashes the original weekday objects.
4. `_common.weekday.__hash__` includes the raw `n`, so `None` and `1` produce different hashes. Dictionary lookup using `b` therefore misses an entry stored under `a`.

Rebuttal check: The underlying weekday hash correctly matches its own stricter equality; the containing delta fails to account for its broader equality rule.

**Divergence:** [The raw weekday hash input](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L549) conflicts with equality at lines 528–529. This **L6 callee contract mismatch** makes equal, unmodified deltas behave as separate keys.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                     # True
{a: "found"}.get(b)         # Expected "found"; observed None
len({a, b})                # Expected 1; observed 2
```

**Remedy:** In `__hash__`, replace line 549’s `self.weekday,` with:

```python
((self.weekday.weekday, self.weekday.n or 1)
 if self.weekday else None),
```

Dry-run: This canonicalizes precisely the weekday variants that delta equality merges. The in-memory remedy preserved distinctions for negative and higher positive occurrences.

**Verification:** Execution-verified on actual source. For all seven weekdays, the original produced 42 failed equality/hash/lookup checks across the `None`, `0`, and `1` variants; the in-memory remedy produced none. The three equal variants also formed a three-element set before the remedy.

## Summary

Both defects silently produce incorrect results: an ordinal date one day early and failed retrieval or deduplication of equal deltas. Minimal remedies passed targeted checks in memory; no files were modified.

Verification used the supplied Python interpreter, `PYTHONDONTWRITEBYTECODE=1`, local `src` imports, and 10-second probe limits. Seven tool calls were used. The full test suite, other supported Python versions, and downstream timezone behavior were not executed.

## Unresolved Investigations

**U1 — Fractional days applied to a plain `date`.** The actual implementation returns `date(2000, 1, 2)` for `date(2000, 1, 2) + relativedelta(days=0.5)`, while applying the normalized delta returns `datetime(2000, 1, 2, 12)`. `_has_time` excludes fractional days, allowing `date + timedelta` to discard the time component. Tests establish fractional-day behavior for `datetime`, but the inspected evidence does not settle whether plain dates must preserve it. This remains an open contract question, excluded from findings and score; the next check is an authoritative expectation for fractional-day arithmetic on plain dates.