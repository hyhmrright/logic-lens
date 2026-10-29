<!-- run be4f298d9a1f446a99488892b51cd05b; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, supported by `_common.py`, relativedelta tests, documentation, and NEWS. Deep checks covered ordinal-day conversion, weekday equality/hashing, and selected arithmetic controls. Timezone behavior and scalar arithmetic were not exhaustively investigated.  
**Logic Score:** 86/100

> Two concrete bugs were reproduced on the actual local implementation.

## Findings

### 🟡 Warning — **[L3] Day 366 resolves to December 30 in leap years**

**Premises:** The public contract defines `yearday` as the ordinal day within the year. Documentation at `docs/relativedelta.rst:186` and tests at `tests/test_relativedelta.py:170` establish that it selects an absolute date and accounts for leap years. Day 366 of 2000 is December 31.

**Trace:**

1. In [the constructor](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L213), integer `yearday=366` sets `self.leapdays=-1`.
2. The cumulative-day lookup converts 366 into `month=12, day=32`.
3. During [date addition](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L377), `min(31, 32)` clamps the day to December 31.
4. Because December is after February and 2000 is a leap year, the additional `leapdays=-1` subtraction produces December 30.

Rebuttal check: Month-end clamping does run, but it removes the overflow day before the leap adjustment, causing the error.

**Divergence:** **L3 — Boundary Blindspot.** Clamping and leap adjustment together make the valid final ordinal day one day early. A caller selecting a date by day-of-year receives the wrong date.

**Trigger:**

```python
date(2000, 1, 1) + relativedelta(yearday=366)
# Expected: datetime.date(2000, 12, 31)
# Observed: datetime.date(2000, 12, 30)
```

**Remedy:** At line 213, replace:

```python
if yearday > 59:
```

with:

```python
if 59 < yearday < 366:
```

Dry-run: Executed against an in-memory source copy. All 2,924 valid ordinal-day checks passed across 1900, 2000, 2001, and 2004, with two starting dates per year. The original failed the four leap-year day-366 cases. Selected `nlyearday` controls also passed.

**Verification:** ✅ Execution-verified on actual code using Python 3.11.18. The assertions used January 1 plus `n-1` days as the independent ordinal oracle.

### 🟡 Warning — **[L6] Equal weekday deltas fail dictionary lookup**

**Premises:** The public weekday contract explicitly makes omitted `N` equivalent to `+1`. Hashability is supported by `tests/test_relativedelta.py:647` and documented in NEWS. Python’s hashing contract requires equal objects to have equal hashes.

**Trace:**

1. Construct `a = relativedelta(weekday=MO)` and `b = relativedelta(weekday=MO(1))`. Their weekday objects contain `n=None` and `n=1`, respectively.
2. [`relativedelta.__eq__`](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L520) explicitly treats those values as equivalent; all remaining attributes match, so `a == b` is `True`.
3. `relativedelta.__hash__`, at line 549, hashes the raw weekday object.
4. [`weekday.__hash__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/_common.py#L27) hashes `(weekday, n)` without canonicalizing `None` to `1`. The resulting delta hashes differ, so a dictionary cannot find the equal replacement key.

Rebuttal check: Neither object was mutated. Equality already handles the equivalence; hashing omits it.

**Divergence:** **L6 — Callee Contract Mismatch.** Delegating to the weekday hash preserves distinctions that delta equality removes. Equal deltas can occupy separate set entries or fail dictionary/cache lookup.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                    # True
{a: "present"}.get(b)     # Expected: "present"; observed: None
len({a, b})               # Expected: 1; observed: 2
```

**Remedy:** In `relativedelta.__hash__`, replace the tuple’s `self.weekday,` entry at line 549 with:

```python
((self.weekday.weekday, self.weekday.n or 1)
 if self.weekday else None),
```

Dry-run: Executed in memory. All 77 equivalent-pair checks passed across seven weekdays and `N` values `None`, `0`, `1`, `2`, and `-1`. The original failed 42 checks. Distinct weekday occurrences remained unequal.

**Verification:** ✅ Execution-verified on actual code. The probe checked hash agreement, dictionary membership, and set deduplication.

## Summary

Both findings have high confidence and reproduced before their proposed remedies passed in memory. Month-end arithmetic, fractional-day addition, weekday application order, and 16 datetime-difference round trips also passed on both versions.

Verification used the supplied interpreter with `PYTHONDONTWRITEBYTECODE=1`, local `PYTHONPATH=src`, and a 10-second probe limit. Five shell invocations were used, including one rejected heredoc attempt; no files were written, dependencies installed, or services contacted. The full suite was not run. The score describes confirmed findings within the inspected scope, not whole-project correctness.