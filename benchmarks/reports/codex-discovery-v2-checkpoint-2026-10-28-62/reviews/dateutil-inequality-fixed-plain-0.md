<!-- run f63a4bea72fa4c71869cfd7c1fc7a15e; model gpt-6.1-sol; source links normalized only -->

Found three reproducible defects in the supplied implementation.

1. **[P2] `yearday=366` selects December 30 in leap years.**  
   In [relativedelta.py:213](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L213), year-day conversion produces `month=12, day=32, leapdays=-1`. Date application clamps day 32 to December 31, then subtracts one day.

   ```python
   date(2000, 1, 1) + relativedelta(yearday=366)
   # Observed: date(2000, 12, 30)
   # Expected: date(2000, 12, 31)
   ```

   This silently returns the wrong date for a valid ordinal. Comparing all 731 valid year-days across 2000 and 2021 against `January 1 + timedelta(days=n-1)` found exactly this mismatch. It also reproduced for 2020.

2. **[P2] Equal weekday deltas have inconsistent hashes, breaking dictionary and set behavior.**  
   Equality at [relativedelta.py:528](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L528) treats weekday occurrence `None`, `0`, and `1` as equivalent. However, `__hash__` hashes the weekday object directly; its hash includes the unnormalized occurrence value.

   ```python
   a = relativedelta(weekday=MO)
   b = relativedelta(weekday=MO(1))

   a == b                     # Observed: True
   {a: "present"}.get(b)      # Observed: None; expected: "present"
   len({a, b})                # Observed: 2; expected: 1
   ```

   Equal objects must have equal hashes. Equivalent deltas consequently fail cache/dictionary lookup and evade set deduplication. Lookup failure reproduced for all seven weekdays, and each pair produced the same date when applied.

3. **[P2] Multiplication and division discard supported fractions—even with a factor of 1.**  
   [relativedelta.py:501](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L501) converts every scaled relative component to `int`. Division delegates to multiplication, so both operations truncate fractional days, hours, minutes, and seconds.

   ```python
   d = relativedelta(days=0.5)
   d * 1   # Observed: relativedelta()
   d / 1   # Observed: relativedelta()
   ```

   Expected: both retain the half-day interval. Applied to midnight on January 1, 2020, the original delta returns noon, while either result returns midnight. Likewise, `relativedelta(hours=1.5) * 1` loses 30 minutes. Fractional relative values are explicitly supported and tested locally. Equivalent representations also behave differently: half a day disappears when scaled by 1, while 12 hours survives.

These are confirmed defects; no speculative open leads are included. Verification used the actual local implementation with the supplied Python 3.11 interpreter, six 1.17.0, and bytecode writing disabled. Six shell calls were used. No files were modified, dependencies installed, external services accessed, or service/integration tests run. The full test suite and other Python versions were not tested.