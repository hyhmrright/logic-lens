<!-- run 3cdd9f71a94a4887a3e86f0e2bb3f440; model gpt-6.1-sol; source links normalized only -->

Found three confirmed defects in the supplied implementation.

1. **[P2] `yearday=366` produces December 30 in leap years.**  
   In [relativedelta.py:208](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L208), day 366 becomes `month=12, day=32, leapdays=-1`. Applying it clamps December 32 to December 31, then subtracts one day.

   ```python
   date(2020, 1, 1) + relativedelta(yearday=366)
   # Observed: date(2020, 12, 30)
   # Expected: date(2020, 12, 31)
   ```

   I compared every valid ordinal day against `January 1 + timedelta(days=n-1)` in 2000, 2004, 2020, and 2001. The only mismatches were day 366 in the three leap years. Existing tests cover other ordinal days and rejection of 367, but miss this boundary.

2. **[P2] Equal weekday deltas have different hashes, breaking dictionary lookup and set deduplication.**  
   [Equality at line 528](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L528) treats weekday occurrences `None`, `0`, and `1` as equivalent. However, [hashing at line 547](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L547) includes the weekday object directly, whose hash distinguishes those values.

   ```python
   a = relativedelta(weekday=MO)
   b = relativedelta(weekday=MO(1))

   a == b                  # Observed: True
   hash(a) == hash(b)       # Observed: False
   {a: "present"}.get(b)    # Observed: None; expected: "present"
   len({a, b})             # Observed: 2; expected: 1
   ```

   The probe also confirmed that all three equivalent forms remain separate set entries. Equal objects must have equal hashes. The existing hash test only checks that insertion does not raise.

3. **[P2] Inequality incorrectly returns `False` for unrelated types and suppresses comparison fallback.**  
   In [relativedelta.py:567](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L567), `__ne__` negates the direct result of `__eq__`. For unsupported operands, that result is `NotImplemented`; negating it produces `False` on the supplied Python 3.11 runtime.

   ```python
   r = relativedelta(days=1)
   r == 1   # Observed: False
   r != 1   # Observed: False; expected: True
   ```

   Reversed comparisons show the same contradiction. A custom peer with `__ne__` returning `True` was never called for `r != peer`. Python 3.11 also emitted a deprecation warning about using `NotImplemented` in a boolean context.

**Open lead—not counted as a confirmed defect:** fractional days behave differently before and after normalization when added to a `date`. For example, `date(2020, 1, 2) + relativedelta(days=0.5)` returns January 2 as a `date`, while adding its normalized form returns January 2 at noon as a `datetime`. `_has_time` ignores fractional days. This loses information, but the reviewed documentation does not clearly settle the intended behavior for date-only inputs, and standard `date + timedelta` also discards sub-day components.

Verification used targeted local source/test reads and in-memory assertions against the actual workspace module, with `PYTHONDONTWRITEBYTECODE=1`. No full test suite or other Python versions were exercised. Four shell calls were used, including one failed probe launch. No files were modified, dependencies installed, or external services accessed.