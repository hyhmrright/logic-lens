<!-- run 0e2d8e5aaa374b8bb6f8736ba8673368; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`: year-day conversion/application, weekday equality/hashing, and mixed-type comparisons. Supporting evidence: `_common.py`, relevant tests, and documentation. Date-difference construction, normalization, and scalar arithmetic were not exhaustively traced.  
**Logic Score:** 86/100

Three confirmed behavioral defects were reproduced on the actual local implementation. No files were changed.

## Findings

### 🟡 Warning — [L3] Day 366 produces December 30 in leap years

**Premises:** The constructor documents `yearday` as setting the day of the year. `docs/relativedelta.rst:193–213` establishes that this is an absolute ordinal within the given year, accounting for leap years. Day 366 of 2020 is December 31.

**Trace:**

1. At `relativedelta.py:211–214`, `yearday=366` sets `self.leapdays=-1`.
2. The conversion at lines 216–224 stores `month=12, day=32`: December starts after ordinal 334.
3. During addition, lines 377–378 clamp day 32 to December 31.
4. Lines 385–392 then subtract the leap-day adjustment, returning December 30.

Rebuttal check: month-end clamping is documented behavior, but applying it before the ordinal adjustment loses one day. Day 365 also returns December 30, so the two distinct valid ordinals collapse.

**Divergence:** **L3**, at lines 377–386: a valid year-end boundary returns the wrong date.

**Trigger:**

```python
date(2020, 1, 1) + relativedelta(yearday=366)
# Expected: date(2020, 12, 31)
# Observed: date(2020, 12, 30)
```

**Remedy:** Replace the inner `if yearday > 59` block at lines 213–214 with:

```python
                if yearday == 366:
                    yday = 365
                    self.leapdays = 0
                elif yearday > 59:
                    self.leapdays = -1
```

Dry-run: the in-memory replacement returns December 31. Valid ordinals across 1900, 2000, 2019, and 2020 passed; neighboring non-leap-year-day behavior was preserved.

**Verification:** Execution-verified against the actual implementation on Python 3.11.18. The proposed remedy was executed only in memory.

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup and set deduplication

**Premises:** `relativedelta.py:51–56` documents an omitted weekday occurrence as equivalent to `+1`. Equality at lines 528–530 also treats occurrences `None`, `0`, and `1` as equivalent. Hashable objects that compare equal must have equal hashes; `tests/test_relativedelta.py:647–651` explicitly exercises dictionary-key support.

**Trace:**

1. Constructing `relativedelta(weekday=MO)` and `relativedelta(weekday=MO(1))` retains occurrences `None` and `1`.
2. `relativedelta.__eq__`, lines 528–545, returns `True`.
3. `relativedelta.__hash__`, lines 547–565, hashes the unnormalized weekday object.
4. `_common.weekday.__hash__`, lines 27–31, hashes `(weekday, n)`, distinguishing the occurrences. A dictionary lookup with the equal second delta consequently misses.

Rebuttal check: the existing hashability test checks insertion only; it does not check lookup using an equal alternate representation.

**Divergence:** **L6**, at line 549: the delegated weekday hash uses a stricter equivalence relation than `relativedelta` equality. Equal keys can occupy separate set entries or fail dictionary lookup.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                       # True
{a: "value"}.get(b, "MISSING")  # Observed: "MISSING"
len({a, b})                   # Observed: 2; expected: 1
```

**Remedy:** Replace `self.weekday,` at line 549 with:

```python
            ((self.weekday.weekday, self.weekday.n or 1)
             if self.weekday is not None else None),
```

Dry-run: dictionary lookup and set deduplication pass with the in-memory replacement. Checks covered all seven weekdays and equivalent occurrences `None`, `0`, and `1`; occurrences `2` and `-1` remained unequal.

**Verification:** Execution-verified on actual code, including unequal hashes and failed lookup. Remedy verification used an in-memory source copy.

### 🟡 Warning — [L6] Inequality incorrectly negates `NotImplemented`

**Premises:** At lines 520–522, `__eq__` returns `NotImplemented` for unrelated types. That sentinel requests Python’s comparison fallback; it is not an equality result. The tests at lines 316–321 exercise mixed-type equality and reflected comparison support.

**Trace:**

1. `relativedelta() != 19` enters `__ne__` at line 567.
2. Its direct call to `self.__eq__(19)` returns `NotImplemented`.
3. Line 568 evaluates `not NotImplemented`, producing `False` on the supplied Python 3.11 runtime instead of preserving comparison fallback.
4. Thus both `relativedelta() == 19` and `relativedelta() != 19` evaluate to `False`.

Rebuttal check: a separate operand implementing `__ne__` to return `True` was also tested; the delta’s premature `False` prevents that reflected method from deciding the result.

**Divergence:** **L6**, at line 568: `__ne__` assumes its callee always returns a Boolean. Inequality with unrelated values is incorrect.

**Trigger:**

```python
relativedelta() != 19
# Expected: True
# Observed: False
```

The supplied runtime additionally emits a `DeprecationWarning` about using `NotImplemented` in a Boolean context.

**Remedy:** Replace `__ne__` with:

```python
    def __ne__(self, other):
        result = self.__eq__(other)
        return NotImplemented if result is NotImplemented else not result
```

Dry-run: the in-memory replacement passed comparisons with integers, `None`, plain objects, and a custom reflected comparator. Same-type equal and unequal comparisons also passed.

**Verification:** Execution-verified on actual code. The remedy passed focused in-memory checks.

## Summary

The confirmed consequences are an incorrect leap-year date, failed lookup/deduplication of equal deltas, and incorrect mixed-type inequality. All three failing assertions passed after the proposed changes were applied solely in memory, alongside 2,955 neighboring checks.

Verification used the supplied interpreter, local `src`, `PYTHONDONTWRITEBYTECODE=1`, and a 10-second alarm per probe. Seven shell calls were used; no repository suite, services, or integration tests were run. No unresolved candidate is presented as a defect. The score describes confirmed findings within this inspected slice; its deduction is capped once per L-code per module, so the two L6 findings share one deduction.