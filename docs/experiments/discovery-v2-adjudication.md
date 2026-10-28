# Revision-2 adjudication notes

The target obligations were recorded in `evals/discovery/catalog-v2.json` before
model execution. The following decisions explain source adjudication of additional
claims; these are judgments by the implementing assistant, not independent labels.

- **Date rollover versus time-only midnight:** `isoparse(date + T24:00)` losing a
  day is the selected target. The repaired implementation instead introduces a
  separate `parse_isotime(24:00)` failure by reparsing after normalizing its list.
  That repaired-side discovery is valid, not a target false alarm.
- **Specific rejection versus general strictness:** dateutil's parent explicitly
  disclaims stable rejection strictness. Its mixed-delimiter expected-failure tests
  establish a specific rejection obligation, so those failures count. Generic claims
  that malformed week 53, embedded offset signs, or incomplete time components must
  be rejected do not have that specific support and are recorded as unestablished
  assertions when presented as bugs. Their observed outputs are reproducible; their
  required rejection is the unsettled part. Explicit open leads are not penalized.
  These are not conclusively disproved findings. Report this ambiguity rather than
  equating zero disproved findings with perfect precision.
- **Documentation corrections:** an accurate observation that `YYYYMM` is advertised
  but intentionally rejected by the parent tests is not an additional behavioral
  defect and is not a false assertion. A definite parser-bug claim despite that
  unresolved contract would need separate evidence.
- **Promotion versus changed release components:** the selected semver-diff target
  incorrectly returns patch/minor after actual major/minor component changes. A
  different claim about promoting `1.1.0-pre` to `1.1.1` is not settled by the parent
  contract: same-main promotion is explicitly tested, but the asserted rule retaining
  minor classification across a later patch is not. Its result is reproducible but
  its desired classification remains unestablished. An unresolved account of that
  question is excluded from both findings and unsupported-assertion totals.
- **Build metadata families:** malformed repeated build suffixes, a generated `-0`
  swallowed by ordinary metadata, and long-identifier tails becoming release digits
  are different behavioral failures. Only the last matches the selected target.
  Sharing an upstream patch does not make every metadata finding a target detection.
- **Intersection witnesses:** two ranges both accepting a concrete version prove a
  reported false-negative intersection. Argument-order disagreement violates the
  symmetry of intersection. Explicit null-set and adjacent-stable-version gap checks
  corroborate false positives; parent default matching excludes unrequested prereleases.
  Explicitly unresolved intersection leads do not count even where the evaluator
  later establishes that behavior independently.
- **Additional counts:** distinct behavior classes are deduplicated across reports.
  Several intersection classes share implementation causes; one finding can describe
  several classes. These counts must not be presented as independent root causes,
  exhaustive recall, or a substitute for the preregistered target endpoint.
- **Compact ordinal dates with spaces:** existing ordinal fixtures establish both
  compact and extended ordinal representations, and the constructor documents any
  single date/time separator by default. `2017123 1230` must therefore agree with
  `2017-123 1230` (May 3 at 12:30). Both frozen source variants instead return
  December 3 at 23:00 for the compact form: the common parser consumes the ordinal's
  final digit plus space as a day, and the wrapper skips the first hour digit.
  This is a confirmed additional valid-input defect, distinct from midnight rollover.
  The report's explicitly unresolved numeric-separator ambiguity is not counted.

`additional_probes_v2.py` contains real-source assertions for established behavior
classes and a separately marked diagnostic with an unestablished classification
oracle. Failure alone never establishes an oracle. Python probes assert the imported
module belongs to the exported workspace. Evaluator probes and future tests are not
copied into the review contexts.
