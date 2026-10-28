<!-- run a94cbed8d44341cfa44c7cd6141a7896; model gpt-6.1-sol; source links normalized only -->

Found three confirmed defects in `src/dateutil/relativedelta.py`.

1. **Equal weekday deltas have different hashes.**  
   [Equality logic](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L528) treats `relativedelta(weekday=MO)` and `relativedelta(weekday=MO(1))` as equal, consistent with the documented weekday behavior. However, [hashing](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L547) uses the raw weekday object, whose hash includes the unnormalized occurrence number.

   **Expected:** Equal deltas have equal hashes and work interchangeably as dictionary keys.  
   **Observed:** For those two deltas, `a == b` was `True`, their hashes differed, `b in {a: "value"}` was `False`, and `len({a, b})` was `2`. Both produced January 8 when applied to January 2, 2024.

   **Consequence:** Dictionary lookups can miss equivalent keys, and sets fail to deduplicate equal deltas. The existing hash test only checks that hashing succeeds.

2. **`yearday=366` selects December 30 in leap years.**  
   The [ordinal conversion](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L208) constructs `month=12, day=32, leapdays=-1`. Applying the delta clamps day 32 to December 31, then [subtracts the leap-day adjustment](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L385).

   **Expected:** `date(2024, 1, 1) + relativedelta(yearday=366)` returns `date(2024, 12, 31)`, the year’s 366th day.  
   **Observed:** It returned `date(2024, 12, 30)`. The same error occurred in 2000.

   **Consequence:** Selecting the last ordinal day of a leap year silently returns the preceding day. An in-memory comparison of every valid ordinal against `January 1 + timedelta(days=n-1)` found only this mismatch in 2000 and 2024, and no mismatches in 2001.

3. **Inequality with unrelated types incorrectly returns `False`.**  
   [`__ne__`](https://github.com/dateutil/dateutil/blob/bc90ab44491154ec38b6b5b4d8ec11fb25b434d0/src/dateutil/relativedelta.py#L567) directly negates `self.__eq__(other)`. For unrelated types, `__eq__` returns `NotImplemented`; negating that sentinel produces `False` on the tested Python runtime.

   **Expected:** `relativedelta(days=1) != 19` returns `True`. Unsupported comparisons should preserve `NotImplemented` so Python can perform comparison fallback.  
   **Observed:** Both `relativedelta(days=1) == 19` and `relativedelta(days=1) != 19` returned `False`. Comparing against a plain `object()` showed the same inconsistency. The inequality operations also emitted `DeprecationWarning: NotImplemented should not be used in a boolean context`.

   **Consequence:** Conditions using `!=` against unrelated values take the wrong branch. The existing type-mismatch tests exercise `==`, leaving this path uncovered.

Verification used the actual workspace implementation with the supplied Python 3.11 interpreter, `PYTHONDONTWRITEBYTECODE=1`, and local `src` on `PYTHONPATH`. I used eight shell/tool calls, read supporting local tests and documentation, and ran only in-memory probes. No files were modified, dependencies installed, external services accessed, or full test suite run. Other Python versions were not verified. No additional open leads are included.