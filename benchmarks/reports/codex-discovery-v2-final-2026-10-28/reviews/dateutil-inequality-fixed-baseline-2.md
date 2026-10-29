<!-- run 9a252e9b0e9746c9821e5b1382b25aba; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, focusing on year-day conversion, date application, equality/hashing, and fractional arithmetic. Supporting evidence: `_common.py`, documentation, tests, NEWS, and the timezone conversion caller. Timezone integrations and exhaustive input combinations were not tested.  
**Logic Score:** 79/100

Three confirmed defects were reproduced. The score describes confirmed findings within this inspected scope.

## Findings

### 🟡 Warning — [L3] Day 366 resolves one day early in leap years

**Premises:** `docs/relativedelta.rst:193–213` specifies that `yearday` selects the absolute ordinal day in the given year, including leap-year adjustment. Thus, day 366 of 2020 is December 31.

**Trace:**

1. [Constructor line 214](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L214) sets `leapdays=-1` for `yearday=366`.
2. Lines 216–224 convert it to `month=12, day=32`.
3. Lines 377–378 clamp day 32 to December 31.
4. Lines 385–392 apply the additional leap-day subtraction, returning December 30.

Rebuttal check: ordinary year-days and month-end clamping work; clamping does not compensate for this extra subtraction.

**Divergence:** L3 at the interaction between year-day conversion and day clamping: valid day 366 collapses onto day 365. A date selected by this ordinal is one day early.

**Trigger:**

```python
date(2020, 1, 1) + relativedelta(yearday=366)
# Expected: date(2020, 12, 31)
# Observed: date(2020, 12, 30)
```

**Remedy:** Replace line 214 with:

```python
self.leapdays = -1 if yearday < 366 else 0
```

Dry-run: an in-memory patched module passed all 1,828 valid ordinal-day checks across 1900, 2000, 2020, 2021, and 2024.

**Verification:** Execution-verified against the actual local implementation. The same failure occurred for day 366 in 2000 and 2024.

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup

**Premises:** The class documentation at lines 53–56 makes an unspecified weekday occurrence equivalent to `+1`. `__eq__` also equates occurrences `None`, `0`, and `1`. Hashability is explicitly exercised by `tests/test_relativedelta.py:647–651`; equal hashable objects must have equal hashes.

**Trace:**

1. `relativedelta(weekday=MO)` stores a weekday whose `n` is `None`; `MO(1)` stores `n=1`.
2. `__eq__`, lines 528–530, considers these deltas equal.
3. [Hashing at line 549](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L549) includes the raw weekday object.
4. `_common.weekday.__hash__`, lines 27–31, hashes `(weekday, n)` without that equivalence, producing different hashes.

Rebuttal check: neither object was mutated; both were constructed through the public API.

**Divergence:** L6: the enclosing delta’s equality semantics disagree with its weekday dependency’s hashing semantics. Equivalent keys can occupy separate set entries, and dictionary lookup can miss an existing equal key.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))
assert a == b
{a: "stored"}.get(b, "MISSING")
# Expected: "stored"
# Observed: "MISSING"
```

A set containing the `None`, `0`, and `1` variants had three entries despite their equality.

**Remedy:** Replace `self.weekday,` at line 549 with:

```python
(self.weekday.weekday, self.weekday.n or 1)
if self.weekday is not None else None,
```

Enclose that conditional expression in parentheses when splitting it across lines.

Dry-run: the in-memory remedy collapsed all three equivalent variants into one set entry for every weekday; occurrence `2` remained unequal.

**Verification:** Execution-verified against the actual local implementation, including failed dictionary lookup and duplicate set entries.

### 🟡 Warning — [L2] Multiplication and division discard supported fractional values

**Premises:** `NEWS:686–688` explicitly supports fractional relative units. Tests at `tests/test_relativedelta.py:422–449` establish their time contribution, while lines 271–282 exercise scalar multiplication and division. Multiplying or dividing an interval by `1` should preserve that contribution.

**Trace:**

1. `relativedelta(days=1.5)` retains `days` as a float and adds 36 hours to a datetime.
2. [Multiplication lines 495–507](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L495) converts the multiplier to `1.0`, then evaluates `int(1.5 * 1.0)`, yielding `1`.
3. The new delta therefore adds only 24 hours.
4. Division at lines 567–573 delegates to the same multiplication implementation.

Rebuttal check: this occurs with multiplier `1`, so it requires neither fractional calendar months nor a rounding decision about the multiplier.

**Divergence:** L2 at lines 503–507: coercion to `int` silently removes supported fractional days, hours, minutes, seconds, and microseconds.

**Trigger:**

```python
base = datetime(2020, 1, 1)
delta = relativedelta(days=1.5)

base + delta       # 2020-01-02 12:00
base + delta * 1   # 2020-01-02 00:00
base + delta / 1   # 2020-01-02 00:00
```

Both scaled results should retain the original noon result.

**Remedy:** At lines 503–507, replace each `int(self.<field> * f)` with `self.<field> * f` for `days`, `hours`, `minutes`, `seconds`, and `microseconds`. Retain the integer conversions for years and months.

Dry-run: the in-memory remedy passed 60 scaling checks covering positive, negative, zero, integral, and fractional values.

**Verification:** Execution-verified against the actual local implementation for all five affected fields and both identity operations.

## Summary

All three reproductions passed after applying the proposed changes solely to an in-memory module. Seventeen unchanged existing test methods also passed against both implementations; they were executed in isolation without pytest fixtures, so this was not a full-suite run.

Probes used Python 3.11.18, local `src/`, `PYTHONDONTWRITEBYTECODE=1`, and 10-second bounds. No files were modified, dependencies installed, or external services accessed.

## Unresolved Investigations

**U1 — Fractional days applied to plain dates:** `date(2020,1,1) + relativedelta(days=0.5)` returns January 1, while applying its normalized equivalent returns January 1 at noon. Existing fractional tests use datetimes. The required result type for fractional-day operations on plain dates remains unestablished; this is an open contract question, not a confirmed defect.