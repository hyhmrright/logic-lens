<!-- run 063284f1d53a48d492e4cf83b19709e5; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, supported by `_common.weekday`, local documentation, tests, and selected timezone callers. Deep traces focused on year-day conversion, hashing, and inequality.  
**Logic Score:** 86/100

Three concrete defects were reproduced. The score describes confirmed findings within this scope; repeated L6 findings in this module receive one deduction.

## Findings

### 🟡 Warning — [L3] Year-day 366 resolves to December 30 in leap years

Premises: The documented `yearday` argument selects an absolute day within the year. [The documentation](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/docs/relativedelta.rst#L193) and `testYearDay` establish that leap days count. In 2000, day 366 is December 31.

Trace:

1. At `relativedelta.py:213–224`, `relativedelta(yearday=366)` sets `leapdays=-1`, `month=12`, and `day=32` (`366 - 334`).
2. At lines 377–378, addition clamps day 32 to December 31.
3. At lines 385–388, the leap-year adjustment subtracts another day, producing December 30. Rebuttal check: day clamping does execute, but it precedes the subtraction and therefore does not prevent the error.

Divergence: **L3** — the terminal year-day boundary receives an extra leap-day correction. The requested date is silently one day early.

Trigger:

```python
date(2000, 1, 1) + relativedelta(yearday=366)
# Expected: date(2000, 12, 31)
# Observed: date(2000, 12, 30)
```

Remedy: At [line 213](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L213), replace the condition with:

```python
if 59 < yearday < 366:
```

Dry-run: This preserves the correction for days 60–365 and allows day 366 to clamp to December 31.

Verification: Reproduced on the actual implementation. The in-memory remedy passed every valid year-day and non-leap-year-day check across 1900, 1999, 2000, and 2004: 2,922 assertions combined. Non-leap-year handling of `yearday=366` is outside this finding’s claim.

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup

Premises: Hashable objects that compare equal must have equal hashes. The class documentation explicitly makes an unspecified weekday occurrence equivalent to `+1`; `__eq__` also treats occurrence `0` as equivalent. Local `testHashable` demonstrates intended dictionary-key support.

Trace:

1. At `relativedelta.py:528–529`, `relativedelta(weekday=MO)` compares equal to `relativedelta(weekday=MO(1))`.
2. At lines 547–549, `relativedelta.__hash__` hashes the original weekday object.
3. At `_common.py:27–31`, `weekday.__hash__` hashes `(weekday, n)` without canonicalizing `n`. Consequently, equal deltas receive different hashes and dictionary lookup misses. Rebuttal check: the outer equality normalization never reaches the hash calculation.

Divergence: **L6** — delegation to `weekday.__hash__` supplies stricter occurrence semantics than `relativedelta.__eq__`. Dictionaries cannot reliably retrieve an equal key, and sets retain equal duplicates.

Trigger:

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                       # True
{a: "stored"}.get(b)          # Expected "stored"; observed None
len({a, b})                  # Expected 1; observed 2
```

Remedy: Replace the first tuple element, `self.weekday`, at [line 549](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L549) with:

```python
((self.weekday.weekday, self.weekday.n or 1)
 if self.weekday is not None else None),
```

Dry-run: This canonicalizes `None`, `0`, and `1` consistently with equality while retaining distinct weekday numbers and other occurrences.

Verification: Reproduced using actual dictionary lookups and sets. The in-memory remedy passed equivalent-key lookup, equal-hash, and set-deduplication checks for all seven weekdays, including occurrences `None`, `0`, and `1`.

### 🟡 Warning — [L6] Inequality consumes `NotImplemented` as a boolean

Premises: At `relativedelta.py:521–522`, `__eq__` explicitly returns `NotImplemented` for unrelated types, allowing Python’s comparison dispatch to continue. Local comparison tests exercise unsupported types, but use `==` only.

Trace:

1. Evaluating `relativedelta(days=1) != 19` enters `__ne__` at line 567.
2. Its direct call to `self.__eq__(19)` returns `NotImplemented`.
3. Line 568 applies `not` to that sentinel. On Python 3.11, it is truthy, so the result is `False`, bypassing normal comparison fallback. Rebuttal check: returning `NotImplemented` from `__eq__` does not help when `__ne__` immediately converts it.

Divergence: **L6** — `__ne__` assumes its callee always returns a boolean. Both equality and inequality with ordinary unrelated objects return `False`, so inequality checks can incorrectly reject mismatches.

Trigger:

```python
r = relativedelta(days=1)
r == 19    # False
r != 19    # Expected True; observed False
```

Remedy: Replace [the method at line 567](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L567) with:

```python
def __ne__(self, other):
    result = self.__eq__(other)
    if result is NotImplemented:
        return NotImplemented
    return not result
```

Dry-run: Same-type comparisons retain their behavior; unsupported comparisons continue through Python’s dispatch.

Verification: Reproduced against `19`, `None`, and `object()`. The in-memory remedy passed those cases in both operand orders, same-type comparisons, and a custom reflected-comparison check.

## Summary

All three defects and their minimal remedies were verified through bounded, in-memory execution of local source using Python 3.11.18 with bytecode writing disabled. No files were changed, dependencies installed, or external services used.

Used 7 of 10 permitted tool calls. Verification covered targeted assertions and arithmetic controls, not the full test suite, other Python versions, or exhaustive timezone/fold, mutation, and scaling behavior. No additional concrete open leads were retained.