<!-- run d96142ca8fc44fae9dc508da65e89a23; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, with supporting evidence from `_common.py`, relativedelta tests, documentation, and selected callers. Deep traces cover year-day conversion, equality/hashing, and inequality dispatch; other arithmetic paths were not exhaustively verified.  
**Logic Score:** 86/100

> Three concrete defects were reproduced on the supplied implementation. No files were modified.

## Findings

### 🟡 Warning
**[L3] — Leap-year day 366 resolves one day early**

**Premises:** The documented `yearday` argument selects the ordinal day within the destination year. [Documentation](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/docs/relativedelta.rst#L186) and `testYearDay` establish that leap years count February 29. Consequently, day 366 of 2020 is December 31.

**Trace:**

1. [`__init__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L211) receives integer `yearday=366` and sets `leapdays=-1`.
2. Its cumulative-day table converts 366 into `month=12, day=32`.
3. [`__add__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L377) clamps day 32 to December 31, then applies the leap-year adjustment of −1 day.

Rebuttal check: Clamping does not preserve the intended ordinal here; it removes the extra day before the leap adjustment also subtracts one.

**Divergence:** **L3:** The boundary value 366 loses a day during clamping. The observable result is December 30, identical to `yearday=365`.

**Trigger:**

```python
date(2020, 1, 1) + relativedelta(yearday=366)
# Expected: date(2020, 12, 31)
# Observed: date(2020, 12, 30)
```

**Remedy:** Replace the `elif yearday:` block at lines 211–214 with:

```python
            elif yearday:
                yday = yearday
                if yearday == 366:
                    yday = 365
                    self.leapdays = 0
                elif yearday > 59:
                    self.leapdays = -1
```

Dry-run: December 31 is represented directly, avoiding clamping followed by subtraction.

**Verification:** ✅ Reproduced on actual code. The in-memory remedy passed this trigger and every valid ordinal day in 1999, 2000, 2001, and 2004. Representative `nlyearday` and ordinary arithmetic controls also passed.

### 🟡 Warning
**[L6] — Equal weekday deltas fail dictionary lookup and set deduplication**

**Premises:** The public contract treats unspecified weekday occurrence as `+1`. [`__eq__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L528) also treats occurrence `0` as equivalent. Hashable equal objects must have equal hashes; `testHashable` explicitly exercises dictionary-key support.

**Trace:**

1. Construct deltas with `weekday=MO`, `MO(1)`, and `MO(0)`.
2. `relativedelta.__eq__` considers all three equal.
3. [`relativedelta.__hash__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L547) hashes the unnormalized weekday object.
4. [`weekday.__hash__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/_common.py#L27) hashes `(weekday, n)`, preserving the distinction between `None`, `1`, and `0`.

Rebuttal check: Date application normalizes these occurrences, but hashing has no corresponding normalization.

**Divergence:** **L6:** The enclosing class uses a component hash whose equivalence rules differ from its own equality rules. An equal key can miss an existing dictionary entry, and a set can retain equal duplicates.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                       # True
{a: "saved"}.get(b, "MISSING") # Observed: "MISSING"; expected: "saved"
len({a, b})                  # Observed: 2; expected: 1
```

**Remedy:** Replace `self.weekday,` at line 549 with:

```python
            (self.weekday.weekday, self.weekday.n or 1)
            if self.weekday is not None else None,
```

Dry-run: Equivalent weekday occurrences contribute identical tuple members.

**Verification:** ✅ Reproduced on actual code. The in-memory remedy restored dictionary lookup, equal hashes, and set deduplication for `MO`, `MO(0)`, and `MO(1)`; controls included absent weekdays and `MO(2)`.

### 🟡 Warning
**[L6] — Inequality consumes `NotImplemented` instead of allowing fallback**

**Premises:** [`__eq__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L520) returns `NotImplemented` for unrelated types. Python comparison dispatch uses this sentinel to try the other operand and then its fallback behavior.

**Trace:**

1. Evaluate `relativedelta() != 19`.
2. [`__ne__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L567) directly calls `self.__eq__(19)`, receiving `NotImplemented`.
3. It evaluates `not NotImplemented`. On the supplied Python 3.11 runtime, the sentinel is truthy, so this returns `False` and ends comparison dispatch.

Rebuttal check: Returning a concrete boolean prevents reflected comparison or fallback from correcting the result.

**Divergence:** **L6:** `__ne__` assumes `__eq__` always returns a boolean. An unrelated integer is reported as neither equal nor unequal.

**Trigger:**

```python
relativedelta() == 19  # False
relativedelta() != 19  # Observed: False; expected: True
```

**Remedy:** Replace `__ne__` with:

```python
    def __ne__(self, other):
        result = self.__eq__(other)
        if result is NotImplemented:
            return NotImplemented
        return not result
```

Dry-run: Unsupported comparisons resume normal dispatch; supported comparisons retain boolean inversion.

**Verification:** ✅ Reproduced on actual code. The in-memory remedy passed the integer trigger, equal/unequal delta controls, and a reflected-inequality control.

## Summary

All three defects were reproduced using the supplied Python 3.11.18 interpreter and six 1.17.0, with `PYTHONDONTWRITEBYTECODE=1`, local `src` imports, and a 10-second alarm. Proposed remedies were executed only as an in-memory source variant; the existing test suite and integration tests were not run, so broader regression coverage is unverified.

The score measures confirmed findings in the inspected slice, with the two L6 findings sharing one deduction under the scoring rule. It does not establish whole-file correctness.

## Unresolved Investigations

Conditional `leapdays` arithmetic remains an open lead: negation and multiplication preserve this field, but the inspected contracts do not establish whether that modifier should change sign or scale. Further contract or caller evidence is needed before treating that behavior as a defect; it does not affect the score.