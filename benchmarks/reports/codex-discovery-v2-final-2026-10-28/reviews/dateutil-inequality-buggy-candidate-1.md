<!-- run ec43c753ec9c4d578ee103fce246a94b; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, emphasizing year-day conversion, date application, equality, hashing, and inequality. Supporting evidence: `_common.py`, local documentation, and targeted tests. Seven calls used; no files modified. Arithmetic scaling and timezone-aware differences were not exhaustively reviewed.  
**Logic Score:** 86/100

> Three concrete defects reproduced. The score describes confirmed findings within the inspected paths; the per-module L-code cap applies.

## Findings

### 🟡 Warning

**[L3] — Day 366 selects December 30 in a leap year**

**Premises:** The documented `yearday` contract selects an absolute day within the given year (`docs/relativedelta.rst:186–213`). Existing tests distinguish leap-year ordinal days from `nlyearday` (`tests/test_relativedelta.py:170–190`). Consequently, day 366 of 2020 is December 31.

**Trace:**

1. In [`__init__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L211), `yearday=366` sets `leapdays=-1`.
2. The cumulative-day table converts 366 to `month=12, day=32`.
3. `__add__`, lines 377–378, clamps day 32 to December 31.
4. Lines 385–388 then subtract the leap-day adjustment, returning December 30.

Rebuttal check: Month-end clamping prevents an invalid-date exception but causes the ordinal-day error.

**Divergence:** **L3** — Clamping before applying the leap correction collapses both year-days 365 and 366 onto December 30.

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

Dry-run: The in-memory fix returns December 31; neighboring year-day checks passed.

**Verification:** Reproduced on the actual implementation. Combined in-memory remedies passed 8,768 calendar assertions covering valid `yearday` and `nlyearday` values across eight selected century, leap, and ordinary years.

---

**[L6] — Equal weekday deltas have different hashes**

**Premises:** The public weekday contract treats an omitted occurrence as `+1` (`relativedelta.py:51–56`). `__eq__` additionally treats `0` as equivalent to `1`. Dictionary-key support is explicitly tested at `tests/test_relativedelta.py:647–651`; equal keys must have equal hashes.

**Trace:**

1. Constructing deltas with `MO`, `MO(0)`, and `MO(1)` retains their respective weekday objects.
2. [`__eq__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L528) treats their occurrence values as equivalent.
3. `__hash__`, lines 547–565, hashes the weekday object directly.
4. `_common.weekday.__hash__`, lines 27–31, hashes the raw occurrence value, distinguishing `None`, `0`, and `1`.

Rebuttal check: Equal date-application behavior and delta equality do not repair the dictionary lookup, which uses the differing hashes.

**Divergence:** **L6** — Delegating hashing to the weekday object assumes its equality semantics match the enclosing delta’s semantics. They differ, so equal deltas can occupy separate set entries and miss dictionary lookups.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))
a == b                       # True
{a: "stored"}.get(b)         # Expected "stored"; observed None
len({a, b})                  # Expected 1; observed 2
```

**Remedy:** Replace `self.weekday,` inside `__hash__` at line 549 with:

```python
(self.weekday.weekday, self.weekday.n or 1)
if self.weekday is not None else None,
```

Dry-run: The in-memory fix unified hashes and dictionary lookups for omitted, zero, and first occurrences across all seven weekdays; other occurrence values remained unequal.

**Verification:** Reproduced on actual code, including three equal weekday forms producing three set entries. The proposed hash change passed the stated controls in memory.

---

**[L6] — Inequality incorrectly consumes `NotImplemented`**

**Premises:** `__eq__` deliberately returns `NotImplemented` for unrelated types, enabling reflected comparison. Local tests establish that unrelated integers compare unequal and that unsupported objects may supply their own comparison behavior (`tests/test_relativedelta.py:316–321`).

**Trace:**

1. [`__ne__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L567) directly calls `self.__eq__(other)`.
2. For integer `19`, `__eq__` returns `NotImplemented` at line 522.
3. `not NotImplemented` evaluates to `False` on the supplied Python 3.11 runtime, with a deprecation warning.
4. Returning that boolean prevents reflected inequality or the normal unequal fallback.

Rebuttal check: Returning `NotImplemented` from `__eq__` is correct; the defect occurs when `__ne__` converts it to a boolean.

**Divergence:** **L6** — `__ne__` assumes its callee always returns a boolean. Consequently, both equality and inequality can report false for the same operands.

**Trigger:**

```python
r = relativedelta(year=1)
r == 19       # False
r != 19       # Expected True; observed False
19 != r       # Expected True; observed False
```

**Remedy:** Replace the body of `__ne__` with:

```python
result = self.__eq__(other)
return NotImplemented if result is NotImplemented else not result
```

Dry-run: In-memory checks passed for unrelated integers, strings, dates, `None`, ordinary objects, reflected inequality, and equal/unequal deltas.

**Verification:** Reproduced on actual code under Python 3.11.18. The observed warning and incorrect booleans match the trace.

## Summary

All three defect assertions failed on the original implementation and passed with the combined in-memory remedies. Seventeen selected existing unit-test methods passed against both versions.

Verification used the supplied interpreter, local source imports, bytecode writing disabled, and 10-second probe limits. Existing test bodies ran through an isolated in-memory harness; the full pytest suite, integration tests, and other Python versions were not run.

## Unresolved Investigations

**U1 — Fractional days with date-only operands:** `_has_time` ignores fractional `days`, while inspected fractional-day tests use `datetime` operands. Whether date-only input should preserve sub-day precision through promotion remains unestablished. Resolve that contract before treating possible truncation as another defect; this lead does not affect the score.