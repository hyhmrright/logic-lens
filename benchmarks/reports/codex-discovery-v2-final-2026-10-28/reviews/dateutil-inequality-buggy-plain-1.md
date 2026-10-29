<!-- run 43d8ae1322f1464188198eb1b84f78da; model gpt-6.1-sol; source links normalized only -->

Found three confirmed defects.

1. **[P2] Equal weekday deltas fail dictionary lookup and set deduplication.**  
   [`__hash__`, line 547](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L547)

   ```python
   a = relativedelta(weekday=MO)
   b = relativedelta(weekday=MO(1))
   ```

   Expected: equal objects have equal hashes, `{a, b}` contains one entry, and `{a: "present"}[b]` succeeds.

   Observed: `a == b` is `True`, their hashes differ, the set contains two entries, and the dictionary lookup misses.

   Evidence: `__eq__` at lines 528–530 treats weekday occurrences `None`, `0`, and `1` as equivalent. `__hash__` hashes the weekday object unchanged; its implementation in `src/dateutil/_common.py:27` hashes the raw occurrence value. Probes reproduced the failure for all seven weekdays with both implicit and zero occurrences compared against occurrence 1.

2. **[P2] `yearday=366` selects December 30 in leap years.**  
   [Year-day conversion, line 208](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L208)

   ```python
   date(2024, 1, 1) + relativedelta(yearday=366)
   ```

   Expected: `date(2024, 12, 31)`, the leap year’s 366th day.

   Observed: `date(2024, 12, 30)`. Days 365 and 366 both select December 30.

   Evidence: the constructor converts 366 into `month=12, day=32, leapdays=-1`. During application, line 377 clamps day 32 to December 31, then lines 385–386 subtract the leap day. The documented ordinal-day behavior and existing `testYearDay` cases support the expected interpretation.

   An exhaustive probe checked **2,193 valid year-day inputs** across 1999, 2000, 2023, 2024, 2100, and 2400. The only mismatches were day 366 in the three leap years.

3. **[P2] Cross-type inequality incorrectly returns `False`.**  
   [`__ne__`, line 567](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L567)

   ```python
   a = relativedelta(days=1)
   a == 19  # False
   a != 19  # False
   ```

   Expected: `a != 19` is `True`.

   Observed: both comparisons return `False`; `19 != a` also returns `False`. A foreign object whose own `__ne__` returns `True` produces asymmetric results: `a != foreign` is `False`, while `foreign != a` is `True`.

   Evidence: `__eq__` correctly returns `NotImplemented` for unsupported types, but `__ne__` directly negates that sentinel. On the supplied Python 3.11 runtime, this yields `False` and emits a `DeprecationWarning`, preventing comparison fallback.

Verification used the actual workspace module, the supplied interpreter, and `PYTHONDONTWRITEBYTECODE=1`. Local documentation and relevant tests were inspected; the full test suite and other Python versions were not run. No source files were changed, dependencies installed, or external services accessed. No additional unverified leads are reported.