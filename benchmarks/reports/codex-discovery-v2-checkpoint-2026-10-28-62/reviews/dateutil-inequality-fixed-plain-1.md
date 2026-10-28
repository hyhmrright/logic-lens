<!-- run 4185869239f04f7db177ff009e99ec1c; model gpt-6.1-sol; source links normalized only -->

Found three reproducible defects, all **P2**.

1. **Equal weekday deltas have different hashes, breaking dictionary and set behavior.**  
   [relativedelta.py:547](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L547)

   `__eq__` treats weekday occurrence values `None`, `0`, and `1` as equivalent (lines 528–530), but `__hash__` hashes the original weekday object, whose hash distinguishes those values.

   Reproduced:
   ```python
   a = relativedelta(weekday=MO)
   b = relativedelta(weekday=MO(1))

   a == b                           # True
   {a: "present"}.get(b, "MISSING")  # "MISSING"
   len({a, b})                      # 2
   ```
   **Expected:** Equal objects have equal hashes, allowing interchangeable dictionary lookups and set deduplication. **Observed:** Lookups miss and sets retain equivalent values. Probes reproduced this for all seven weekdays, including occurrence `0`, without mutating any objects.

2. **`yearday=366` returns December 30 in leap years.**  
   [relativedelta.py:216](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L216)

   The year-day conversion creates `month=12, day=32, leapdays=-1`. During application, lines 377–378 clamp day 32 to December 31; lines 385–386 then subtract the leap-day adjustment.

   ```python
   date(2020, 1, 1) + relativedelta(yearday=366)
   # Observed: date(2020, 12, 30)
   # Expected: date(2020, 12, 31)
   ```
   The documented meaning is the absolute day of the year. Consequently, days 365 and 366 incorrectly resolve to the same date in leap years. Across 582 selected boundary checks covering all 97 leap years from 2000 through 2399, all 97 mismatches were for day 366.

3. **Multiplication and division silently discard supported fractional time values—even when scaling by one.**  
   [relativedelta.py:501](https://github.com/dateutil/dateutil/blob/68994217fbe253835989e7c1e3eeef5c653088d1/src/dateutil/relativedelta.py#L501)

   `__mul__` applies `int()` separately to each relative field. Division delegates to multiplication (line 573). Fractional days, hours, minutes, and seconds are supported by the constructor and explicitly tested locally, but these operators truncate them instead of preserving their duration.

   ```python
   dt = datetime(2020, 1, 1)
   rd = relativedelta(days=1.5)

   dt + rd        # 2020-01-02 12:00
   dt + (rd * 1)  # 2020-01-02 00:00
   dt + (rd / 1)  # 2020-01-02 00:00
   ```
   **Expected:** Multiplying or dividing by one preserves the applied result. **Observed:** Both lose 12 hours here. All 16 probes covering positive and negative fractional days, hours, minutes, and seconds changed the resulting datetime. Normalizing first preserved the original result. Even `relativedelta(hours=1) * 0.5` becomes an empty delta rather than 30 minutes.

These are confirmed defects; no additional open leads are included.

Verification used the supplied local source, Python 3.11, and the provided `six` dependency with bytecode writing disabled. I used seven shell/tool calls, made no file changes, and accessed no external services. Verification was limited to targeted in-memory probes; I did not run the full test suite or test other Python versions.