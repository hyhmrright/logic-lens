<!-- run b3d36ca5c2ce485f8fd92af3fecbd073; model gpt-6.1-sol; source links normalized only -->

Found three implementation defects and one documentation defect. All examples below were reproduced against the workspace’s implementation.

1. **[P2] `parse_isotime()` discards midnight normalization.**  
   At [isoparser.py:176](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L176), the method changes hour `24` to `0`, then reparses the original input when constructing `time`, discarding that change.

   **Expected:** `parse_isotime("24:00")` returns `datetime.time(0, 0)`, consistent with the documented midnight support and the explicit normalization.  
   **Observed:** `ValueError: hour must be in 0..23`.

   The same failure occurs for `"24"`, `"24:00:00.000000"`, `"24:00Z"`, and `"24:00+05:30"`. Ordinary `"00:00"` succeeds. The datetime entry point correctly advances `"2014-04-11T24:00"` to April 12.

2. **[P2] Signed offset components bypass validation and can reverse the offset’s sign.**  
   At [isoparser.py:395](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L395), hour and minute slices are passed directly to `int()`. Negative components are accepted because the subsequent checks enforce only upper bounds.

   **Expected:** Reject offsets containing additional signs with `ValueError`; the documented formats have one leading sign followed by unsigned hour/minute digits.  
   **Observed:**

   | Input | Returned offset |
   |---|---|
   | `"+00-30"` | UTC−00:30 |
   | `"+-1:00"` | UTC−01:00 |
   | `"+01-30"` | UTC+00:30 |

   This propagates through `isoparse()`: `"2014-04-11T12:00+00-30"` becomes `12:00−00:30`, corresponding to **12:30 UTC**. Malformed input therefore produces a usable timestamp with unintended arithmetic rather than an error. Valid `"+01:30"` and `"+0130"` both correctly return UTC+01:30.

3. **[P2] Week 53 is accepted for ISO years that contain only 52 weeks.**  
   At [isoparser.py:317](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L317), validation checks only `1 ≤ week ≤ 53`. The calculation then adds the requested weeks without checking whether week 53 exists in that ISO year.

   **Expected:** Reject `"2014-W53-1"` because ISO year 2014 has no week 53.  
   **Observed:** Both `isoparse()` and `parse_isodate()` return December 29, 2014, whose `isocalendar()` is **`(2015, 1, 1)`**. The basic form `"2014W531"` behaves identically. `"2017-W53-7"` similarly becomes January 7, 2018, in ISO week 1 of 2018.

   Python’s `date.fromisocalendar(2014, 53, 1)` rejects the input. As a control, the valid `"2015-W53-1"` correctly returns December 28, 2015.

   **Qualification for findings 2–3:** The parser explicitly disclaims stable strictness for invalid inputs at [isoparser.py:124](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L124). These are validation defects, not evidence of a compatibility regression or incorrect parsing of valid ISO input.

4. **[P3] The documentation advertises unsupported `YYYYMM` input.**  
   [isoparser.py:75](https://github.com/dateutil/dateutil/blob/424a438b3791962e50590410972fdb0ebfd7b4a2/dateutil/parser/isoparser.py#L75) lists both `YYYY-MM` and `YYYYMM` as supported.

   **Expected from that documentation:** `"201204"` parses as April 1, 2012.  
   **Observed:** `ValueError: Invalid ordinal day`; `"2012-04"` succeeds.

   The implementation deliberately rejects the basic year-month form, and [test_isoparser.py:239](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L239) explicitly labels it invalid. This supports correcting the documentation rather than assuming the parser should accept it.

**Open leads and test evidence:** Mixed separators (`"12:3015"`) and a trailing colon (`"12:30:"`) are also accepted. Existing tests already mark mixed-separator rejection as an expected failure; I have not elevated these permissiveness cases into additional findings. Separately, [test_isoparser.py:153](https://github.com/dateutil/dateutil/blob/86e33512c41a04b989b14966a722608035a87b51/dateutil/test/test_isoparser.py#L153) incorrectly expects datetime `24:00` to remain on the same date. The implementation’s next-day rollover is correct.

Verification used targeted source reads and in-memory probes on Python 3.11.18 with bytecode disabled. Valid week, ordinal, fractional-second, offset, and year-rollover controls passed. I did not run the full test suite or verify other Python versions. Seven tool calls were used; no files were modified, dependencies installed, or external services accessed.