<!-- run cbc07a6538cb40dfaed318d1b7b32317; model gpt-6.1-sol; source links normalized only -->

Found three reproducible defects.

1. **[P2] Equal weekday deltas have different hashes, breaking dictionary lookup.**  
   In [relativedelta.py:528](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L528), equality treats weekday occurrences `None`, `0`, and `1` as equivalent. However, `__hash__` hashes the original weekday object, whose hash distinguishes those values.

   Observed:
   ```python
   a = relativedelta(weekday=MO)
   b = relativedelta(weekday=MO(1))
   a == b                         # True
   {a: "value"}.get(b, "MISSING")  # "MISSING"
   ```
   Expected: equal objects must have equal hashes, so the lookup should return `"value"`. A set containing the `MO`, `MO(0)`, and `MO(1)` variants retained all three despite their equality.

2. **[P2] `yearday=366` selects December 30 in a leap year.**  
   The conversion at [relativedelta.py:216](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L216) represents ordinal day 366 as `month=12, day=32, leapdays=-1`. Application first clamps day 32 to December 31, then subtracts the leap adjustment.

   Observed:
   ```python
   date(2020, 1, 1) + relativedelta(yearday=366)
   # datetime.date(2020, 12, 30)
   ```
   Expected: `2020-12-31`, the 366th day of 2020. This also makes ordinal days 365 and 366 resolve to the same date. Checking every valid ordinal in 2019 and 2020 against `January 1 + timedelta(days=n-1)` found exactly this mismatch.

3. **[P2] Multiplication and division by 1 discard supported fractional durations.**  
   [relativedelta.py:501](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L501) applies `int()` separately to each scaled component. Division delegates to this multiplication implementation.

   With `base = datetime(2020, 1, 1)`:
   ```python
   delta = relativedelta(hours=0.5)
   base + delta        # 2020-01-01 00:30:00
   base + delta * 1    # 2020-01-01 00:00:00
   base + delta / 1    # 2020-01-01 00:00:00
   ```
   Expected: scaling by 1 preserves the duration. Fractional components are explicitly supported by the local tests in `testAdditionFloatFractionals`. Probes also confirmed loss of 12 hours for `days=1.5` and half a second for `seconds=0.5`.

These are reproduced defects, not open leads. Verification used the specified Python interpreter, `PYTHONDONTWRITEBYTECODE=1`, and the actual workspace module. Only targeted in-memory probes were run; the full test suite and other runtimes were not tested. No files were modified, dependencies installed, or external services accessed.