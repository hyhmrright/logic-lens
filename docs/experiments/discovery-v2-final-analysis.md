# Revision-2 outcome and next design

The complete frozen comparison fails the discovery objective: plain, previous skill
and revised skill each detect 9/12 targets. There is no measured gain from the new
boundary-investigation instructions on this set. This is a result of the frozen
candidate, not a reason to relax the oracle or reclassify nearby metadata defects.
See the [final report](../../benchmarks/reports/codex-discovery-v2-final-2026-10-28/REPORT.md).

## What the surviving miss shows

**Premises:** The selected range defect strips a bounded prefix of a long build
identifier. A remaining digit becomes a release component. Metadata should not change
version precedence. This is a supported valid-input violation with an evaluator-only
before/after probe; ordinary metadata rejection and hyphen `-0` loss are separate.

**Trace:** All three candidate buggy range reports read `classes/range.js`; their
command records also read relevant regular expressions in `internal/re.js`. They
execute real probes and find Comparator initialization, OR prerelease or intersection
violations. Repeat 0 additionally tests ordinary hyphen metadata. Repeats 1 and 2
invest substantial later calls in in-memory remedies and fixture checks. The complete
reports and tool commands are retained in the final artifact. None of the three
accepted reports establishes the bounded long-identifier tail mechanism. Two earlier
attempts for repeat 0 completed model turns but failed process delivery; they remain
failed attempts, not retrospectively accepted reports.

**Divergence:** Access to the relevant source and permission to execute were present.
The proposed boundary mapping still did not reliably generate a distinguishing test
at a representation limit. Successful nearby discoveries led into remedy validation
without covering that remaining hypothesis. These are trace-supported observations;
the experiment does not isolate which prompt clause caused the choices. The fact
that plain and previous-skill runs also miss the target points to a shared search
weakness, rather than evidence that the revised skill made this particular miss worse.

**Trigger:** A bounded normalization transform feeds a parser, but its output is not
checked against the unchanged semantic value across valid representations. A review
can appear productive by finding several unrelated real defects while this path
remains untested. Broad source reading or lists of unusual inputs do not ensure
that a semantic invariant is exercised at the transform's effective boundary.

**Remedy proposed for a future candidate:** Turn the next investigation step into
a small coverage obligation: enumerate the important input transformations actually
present in the code; derive one supported invariant per transformation; select a
small family of valid paired inputs around observed representation/normalization
boundaries; compare an observable semantic result. Use the implementation to choose
boundaries, without embedding project names, numeric limits or known reproductions
in the generic skill. Investigate the highest unresolved obligation before polishing
repairs to existing findings. Keep proof and counterevidence requirements unchanged.
This is a hypothesis, not a demonstrated improvement, and no further skill change
was made during this frozen evaluation.

## Separate discovery from repair effort

The final candidate used 180,633 accepted output tokens versus plain's 102,370.
Its observed median accepted duration was 225.64 versus 149.60 seconds. Delivery
needed retries, and some traces spend their late calls repairing proposed fixes or
running many existing fixtures. Those checks support remedy confidence but do not
establish coverage of another contract. Existing discovery-before-polish guidance
was insufficient to prevent this allocation in several range reviews.

A useful next ablation would keep the same finding evidence requirements while
comparing (a) plain Codex, (b) the frozen candidate, and (c) a compact discovery-first
variant that postpones broad remedy regression checks until initial contract
coverage is recorded. Keep total budget equal. Measure target detections, unsupported
claims, delivery, known tokens and the point at which each hypothesis was tested.
Do not infer causation from this current three-arm comparison or claim that removing
remedy checks is already proven beneficial.

## Validation requirements

These dateutil/node-semver cases are now development evidence. Any next candidate
must be frozen before selecting or inspecting a new set of real defects, with new
projects and defect families, supported independent oracles, identical runtime/tools
and preregistered semantic matching. Include normalization, routing, state transition
and other boundary families rather than just long strings. Keep all selected cases,
repeats, repaired-side defects, failures and exclusions visible. Independent blinded
adjudication would reduce the current author's contract-interpretation bias.

The current reduction in unsupported assertions (15 / 0 / 0) is worth preserving,
but does not demonstrate better bug recall. Additional behavior classes overlap and
have incomplete ground truth; their totals cannot rescue a failed primary endpoint.
There is no justification for a release promotion or another paid automatic tuning
loop on these same cases. Automatic same-plan recovery ends with this complete record.
