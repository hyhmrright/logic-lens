<!-- run 5d51b5bd33a74e7996f5f975aa35e3d0; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, supported by `_common.py`, relativedelta tests/documentation, and selected parser/timezone callers. Deep traces cover ordinal-day conversion, date application, equality, hashing, and inequality. Other arithmetic and timezone combinations were not exhaustively checked.  
**Logic Score:** 86/100

Three confirmed defects reproduced on the actual local implementation. No files were modified.

## Findings

### 🟡 Warning

**[L3] — Leap-year day 366 resolves to December 30**

**Premises:** `yearday` specifies an absolute ordinal within the year, as documented in `docs/relativedelta.rst:186–213` and exercised by `tests/test_relativedelta.py:170–178`. In 2000, ordinal 366 is December 31.

**Trace:**

1. The constructor sets `leapdays=-1` because `366 > 59` at [relativedelta.py:213](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L213).
2. The ordinal conversion produces `month=12, day=32`: `366 - 334`.
3. Date application clamps day 32 to December 31 at [relativedelta.py:377](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L377).
4. Because December is after February and 2000 is a leap year, application subtracts another day, returning December 30.

Rebuttal check: month-end clamping prevents an invalid-date exception but does not preserve the requested ordinal. Ordinal 365 also returns December 30.

**Divergence:** **L3:** the day-366 boundary loses a day through clamping and then receives the ordinary leap-day correction.

**Trigger:**

```python
date(2000, 1, 1) + relativedelta(yearday=366)
# Expected: date(2000, 12, 31)
# Observed: date(2000, 12, 30)
```

**Remedy:** Replace line 214 with:

```python
self.leapdays = -1 if yearday < 366 else 0
```

Dry-run: the in-memory replacement returns December 31; all 1,462 valid ordinals across 1999, 2000, 2004, and 2100 passed the calendar oracle. Selected `nlyearday` controls retained their results.

**Verification:** Reproduced using the actual implementation. Remedy executed only in an in-memory source copy.

---

**[L6] — Equal weekday deltas have different hashes**

**Premises:** The documented weekday forms `MO` and `MO(1)` are equivalent. `relativedelta.__eq__` explicitly considers them equal. Hashability is supported and tested at `tests/test_relativedelta.py:647`; equal hashable keys must share a hash.

**Trace:**

1. Construct `a=relativedelta(weekday=MO)` and `b=relativedelta(weekday=MO(1))`.
2. Equality treats weekday occurrence values `None` and `1` as equivalent at [relativedelta.py:528](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L528).
3. Hashing includes the unnormalized weekday object at [relativedelta.py:547](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L547).
4. `weekday.__hash__`, defined in `_common.py:27`, hashes `(weekday, n)` directly. Consequently, the two deltas receive different hashes.

Rebuttal check: neither object was mutated; constructor normalization does not canonicalize these equivalent weekday forms.

**Divergence:** **L6:** delegation to weekday hashing does not implement relativedelta’s broader equality contract. Dictionary lookup misses an equal key, and sets retain both equal objects.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                         # True
{a: "found"}.get(b, "missing")  # Observed: "missing"; expected: "found"
len({a, b})                    # Observed: 2; expected: 1
```

**Remedy:** Replace `self.weekday,` inside `__hash__` with:

```python
((self.weekday.weekday, self.weekday.n or 1)
 if self.weekday is not None else None),
```

Dry-run: dictionary lookup and deduplication passed in memory. The equivalent occurrence forms `None`, `0`, and `1` produced one set entry for each of all seven weekdays; occurrence `2` remained unequal.

**Verification:** Reproduced using the actual implementation. Remedy executed in memory.

---

**[L6] — Inequality converts `NotImplemented` to false**

**Premises:** `__eq__` returns `NotImplemented` for unrelated types, permitting Python’s comparison fallback. Existing tests exercise unrelated-type equality and reflected comparison at `tests/test_relativedelta.py:316–321`.

**Trace:**

1. Evaluate `relativedelta(year=1) != 19`.
2. `__ne__` calls `__eq__`, which returns `NotImplemented` at [relativedelta.py:520](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L520).
3. [relativedelta.py:568](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L568) evaluates `not NotImplemented`.
4. On the supplied Python runtime, that evaluates to `False`, with a deprecation warning, instead of allowing comparison fallback.

Rebuttal check: a custom right operand’s `__ne__` was also bypassed; it never received the reflected comparison.

**Divergence:** **L6:** `__ne__` assumes its callee always returns a boolean. Unrelated values compare neither equal nor unequal, and reflected inequality behavior is suppressed.

**Trigger:**

```python
r = relativedelta(year=1)
r == 19  # False
r != 19  # Observed: False; expected: True
```

`relativedelta() != None` likewise returned `False`.

**Remedy:** Replace the body of `__ne__` with:

```python
result = self.__eq__(other)
return NotImplemented if result is NotImplemented else not result
```

Dry-run: unrelated-type inequality and reflected comparison passed in memory; same-type equal and unequal controls also passed.

**Verification:** Reproduced using the actual implementation. Remedy executed in memory.

## Summary

All three findings have concrete observed consequences and reproduced triggers. The score deducts seven points for L3 and seven for L6; the supplied scoring rule caps repeated L6 deductions within this module.

Verification used Python **3.11.18**, local `src` on `PYTHONPATH`, `PYTHONDONTWRITEBYTECODE=1`, and 10-second probe alarms. Eight shell executions were used, including one heredoc setup failure subsequently corrected. No dependencies were installed, no files were written, and no external services, integration tests, or full test suite were run. Remedy checks establish the exercised scenarios only.

## Unresolved Investigations

**U1 — Fractional-day application depends on normalization.** With `d=date(2000,1,1)` and `r=relativedelta(days=0.5)`, `d+r` returned January 1 as a `date`, while `d+r.normalized()` returned January 1 at noon as a `datetime`. Fractional datetime arithmetic is tested, but the inspected contracts do not settle fractional arithmetic on plain dates. This remains an open lead without a score deduction; the next check is to establish the required result type and fractional-time preservation for that combination.