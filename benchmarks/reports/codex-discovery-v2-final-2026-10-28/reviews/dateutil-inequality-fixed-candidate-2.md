<!-- run 876e6e2048e24515ac63e848b9732be9; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, supported by `_common.py`, relativedelta tests/documentation, and selected timezone callers. Deep traces covered weekday hashing, ordinal-day conversion, and fractional arithmetic. Timezone integration and exhaustive operator combinations were not tested.  
**Logic Score:** 79/100

Three confirmed defects. The score describes confirmed findings within this inspected scope, not whole-project correctness.

## Findings

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup

**Premises:** The documented weekday contract makes `MO` equivalent to `MO(1)` (`relativedelta.py:51–56`). Dictionary use is explicitly supported by `tests/test_relativedelta.py:647–651`. Equal hashable objects must have equal hashes.

**Trace:**

1. Construct `a = relativedelta(weekday=MO)` and `b = relativedelta(weekday=MO(1))`.
2. `relativedelta.__eq__` at lines 528–530 treats weekday counts `None`, `0`, and `1` as equivalent; therefore `a == b`.
3. [`__hash__` at line 549](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L549) hashes the unmodified weekday object.
4. `_common.weekday.__hash__` at lines 27–31 hashes `(weekday, n)`, distinguishing `None` from `1`.

Rebuttal check: Equality canonicalizes these representations, but hashing has no corresponding normalization. No mutation is needed.

**Divergence:** **L6** — the delegated weekday hash does not implement relativedelta’s broader equality contract. Equal keys receive different hashes, so lookup misses and sets retain duplicates.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))
a == b                    # Expected/observed: True
{a: "present"}.get(b)      # Expected: "present"; observed: None
```

The probe also found that `{a, relativedelta(weekday=MO(0)), b}` has three elements instead of one.

**Remedy:** Replace `self.weekday,` at line 549 with:

```python
(self.weekday.weekday, self.weekday.n or 1) if self.weekday else None,
```

Dry-run: The in-memory replacement passed equality/hash checks across absent weekdays, default/zero/first occurrences, and distinct occurrences.

**Verification:** Reproduced on the actual implementation. The proposed remedy passed the same lookup assertion in memory.

### 🟡 Warning — [L3] Day 366 selects December 30 in leap years

**Premises:** `yearday` selects the absolute ordinal day within the year (`docs/relativedelta.rst:186–219`), including leap-day counting. Thus day 366 of 2024 is December 31.

**Trace:**

1. `relativedelta(yearday=366)` sets `leapdays=-1` at lines 211–214.
2. The conversion at lines 216–224 produces `month=12, day=32`.
3. [`__add__` at lines 377–378](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L377) clamps day 32 to December 31.
4. Lines 385–386 then apply the additional negative leap day, returning December 30.

Rebuttal check: Day 366 is accepted; only values above 366 reach the upper-bound rejection. Neighboring ordinal days reproduce correctly.

**Divergence:** **L3** — month-end clamping consumes the extra day before the leap-year adjustment subtracts another day. The returned date is one day early.

**Trigger:**

```python
date(2024, 1, 1) + relativedelta(yearday=366)
# Expected: date(2024, 12, 31)
# Observed: date(2024, 12, 30)
```

The independent oracle was `date(2024, 1, 1) + timedelta(days=365)`.

**Remedy:** Replace line 214 with:

```python
self.leapdays = -1 if yearday < 366 else 0
```

Dry-run: The in-memory remedy passed every valid ordinal day in 1900, 2000, 2023, and 2024, plus a neighboring `nlyearday` check.

**Verification:** Reproduced on the actual implementation; the remedy passed the original failing assertion in memory.

### 🟡 Warning — [L2] Multiplication and division discard fractional durations

**Premises:** Fractional relative units are supported and retain their duration when applied to datetimes (`tests/test_relativedelta.py:233–246, 416–432`). Scalar multiplication and division are supported at lines 272–282. A scalar of `1` should preserve the duration.

**Trace:**

1. Construct `d = relativedelta(days=0.5)`. Applying it to midnight correctly produces noon.
2. [`__mul__` at line 503](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L503) evaluates `int(0.5 * 1.0)`, producing `0`.
3. The returned delta contains no half-day remainder, so applying it produces midnight.
4. Division follows the same path: `__div__` at lines 567–573 calculates the reciprocal and delegates to `__mul__`.

Rebuttal check: Construction and datetime addition already accept these fractions. The loss occurs specifically during scalar arithmetic and also affects fractional hours, minutes, seconds, and microseconds.

**Divergence:** **L2** — integer conversion truncates supported fractional values. Both multiplication and division silently change the represented duration, even for scalar `1`.

**Trigger:**

```python
base = datetime(2024, 1, 1)
base + relativedelta(days=0.5) * 1
# Expected: 2024-01-01 12:00
# Observed: 2024-01-01 00:00
```

Likewise, `relativedelta(seconds=0.5) / 1` loses the expected 500,000 microseconds.

**Remedy:** Replace the five arguments at lines 503–507 with:

```python
days=self.days * f,
hours=self.hours * f,
minutes=self.minutes * f,
seconds=self.seconds * f,
microseconds=self.microseconds * f,
```

Dry-run: The in-memory remedy preserved multiplication/division by `1` across all five units with positive, negative, zero, and integer values. Existing integer scaling examples also passed.

**Verification:** Both operator paths reproduced on actual code; both passed after the in-memory replacement.

## Summary

The confirmed consequences are missed dictionary lookups, an incorrect leap-year date, and lost fractional durations. Each proposed remedy passed its reproducing assertion and targeted neighboring checks without modifying files.

Verification used the supplied Python 3.11.18 interpreter, `PYTHONDONTWRITEBYTECODE=1`, and `PYTHONPATH=src`; the remedy-checking process had a 10-second bound. Fixes were compiled exclusively in memory. The full test suite and timezone integrations were not run.

## Unresolved Investigations

These leads do **not** affect the score.

- **Fractional days applied to `date`:** `date(2024,1,1) + relativedelta(days=0.5)` returns January 1, while the normalized delta returns a datetime at noon. The mismatch is reproduced, but the documentation does not clearly establish whether date-only operands must preserve sub-day fractions. Next check: establish that contract before proposing a change.
- **`leapdays` on February 29:** Adding `relativedelta(leapdays=1)` leaves February 29 unchanged because line 385 requires `month > 2`. This appears narrower than “post 28 of February” in the docstring, but supporting examples/tests do not resolve the boundary semantics. Next check: establish whether February 29 itself should qualify.