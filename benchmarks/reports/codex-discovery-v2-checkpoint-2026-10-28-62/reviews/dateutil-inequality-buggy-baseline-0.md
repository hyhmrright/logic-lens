<!-- run 11f0a1aaf1bf4b9ab2aac4e3fbb2f2cf; model gpt-6.1-sol; source links normalized only -->

# Logic-Lens Logic Review

**Mode:** Logic Review  
**Scope:** `src/dateutil/relativedelta.py`, with targeted evidence from `_common.py`, `tests/test_relativedelta.py`, `docs/relativedelta.rst`, and `tz/tz.py`. Deep traces covered ordinal-date conversion, weekday equality/hashing, and inequality fallback. Other arithmetic, timezone, and mutation sequences were not exhaustively reviewed.  
**Logic Score:** 86/100

Three confirmed defects reproduced on the actual local implementation.

## Findings

### 🟡 Warning — [L3] Leap-year day 366 resolves to December 30

**Premises:** The documented `yearday` contract selects the ordinal day within the given year (`docs/relativedelta.rst:186–213`). Tests at `tests/test_relativedelta.py:170–178` establish that leap days count toward that ordinal. In 2024, day 366 is December 31.

**Trace:**

1. In [`relativedelta.py:213`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L213), `yearday=366` sets `leapdays=-1`.
2. The cumulative-day conversion computes `month=12`, `day=366-334=32`.
3. During date addition, line 377 clamps day 32 to December 31.
4. Lines 385–392 apply the leap-year adjustment of −1 day, returning December 30.

Rebuttal check: the existing clamp prevents an invalid date exception, but does not preserve the required ordinal. Days 59, 60, and 365 produced their expected dates.

**Divergence:** **L3**, at the interaction between the final ordinal bucket and leap-day adjustment: valid ordinal 366 loses a day after its intermediate day value is clamped.

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

Dry-run: executed in an in-memory source copy. All 1,462 valid ordinal dates across 1900, 2000, 2023, and 2024 passed; sampled `nlyearday` behavior remained unchanged.

**Verification:** Execution-verified against the actual implementation. The proposed remedy was verified separately in memory.

### 🟡 Warning — [L6] Equal weekday deltas fail dictionary lookup

**Premises:** Hashable objects that compare equal must have equal hashes. Dictionary use is explicitly supported by `testHashable` at `tests/test_relativedelta.py:647`. The weekday documentation states that omitting the occurrence number means `+1`.

**Trace:**

1. Construct `a=relativedelta(weekday=MO)` and `b=relativedelta(weekday=MO(1))`.
2. [`relativedelta.py:528–530`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L528) treats occurrence numbers `None` and `1` as equivalent, so `a == b` is `True`.
3. `relativedelta.__hash__` instead hashes the unnormalized weekday object.
4. `_common.weekday.__hash__` hashes `(weekday, n)`, distinguishing `(0, None)` from `(0, 1)`. The resulting delta hashes differ, and dictionary lookup misses.

Rebuttal check: this requires no mutation, concurrency, or unsupported input. Both objects are freshly constructed with documented weekday forms.

**Divergence:** **L6**, at `relativedelta.py:549`: delegating hashing to the raw weekday representation does not honor the broader equivalence implemented by `relativedelta.__eq__`.

**Trigger:**

```python
a = relativedelta(weekday=MO)
b = relativedelta(weekday=MO(1))

a == b                       # Observed: True
{a: "found"}.get(b, "MISSING") # Expected: "found"; observed: "MISSING"
len({a, b})                  # Expected: 1; observed: 2
```

**Remedy:** Replace the `self.weekday,` entry at line 549 with:

```python
(self.weekday.weekday, self.weekday.n or 1)
if self.weekday is not None else None,
```

Dry-run: the in-memory remedy passed dictionary lookup and set deduplication for all seven weekdays using occurrence numbers `None`, `0`, and `1`; occurrence `2` remained unequal.

**Verification:** Execution-verified against the actual implementation, including differing hashes and failed dictionary lookup. Remedy verification used an in-memory copy.

### 🟡 Warning — [L6] Inequality converts `NotImplemented` to `False`

**Premises:** `relativedelta.__eq__` explicitly returns `NotImplemented` for foreign types, permitting Python’s comparison fallback. Existing tests at `tests/test_relativedelta.py:316–321` support foreign-type comparison. That sentinel must be propagated rather than interpreted as a comparison result.

**Trace:**

1. Evaluate `relativedelta() != 19`.
2. [`relativedelta.py:568`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L568) directly calls `self.__eq__(19)`.
3. Line 522 returns `NotImplemented`.
4. `not NotImplemented` evaluates to `False` on Python 3.11, suppressing comparison fallback.

Rebuttal check: same-type inequality works, but that branch never encounters the sentinel. A foreign object with its own `__ne__` also had its comparator bypassed.

**Divergence:** **L6**, at line 568: `__ne__` assumes `__eq__` always returns a Boolean. Unequal foreign values consequently compare as neither equal nor unequal.

**Trigger:**

```python
relativedelta() == 19  # Observed: False
relativedelta() != 19  # Expected: True; observed: False
```

**Remedy:** Replace the method body with:

```python
result = self.__eq__(other)
return NotImplemented if result is NotImplemented else not result
```

Dry-run: the in-memory remedy passed comparisons against integers, `None`, and plain objects; restored a foreign object’s `__ne__` fallback; and preserved same-type equality and inequality.

**Verification:** Execution-verified on the actual implementation. Python 3.11 also emitted `NotImplemented should not be used in a boolean context`. Remedy checks passed separately.

## Summary

The confirmed consequences are an incorrect calendar date, failed lookup of an equal dictionary key, and incorrect foreign-type inequality. The score reflects these inspected paths, with one deduction per unique L-code in this module: L3 and L6.

Probes used the supplied Python interpreter (3.11.18), local `src` imports, `PYTHONDONTWRITEBYTECODE=1`, and a 10-second alarm, without mocks. Eight tool calls were used; no files were modified, dependencies installed, external services accessed, or repository/service/integration test suites run. No additional open lead was retained; the scope omissions above remain unreviewed.