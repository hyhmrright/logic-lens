# Logic-Lens — Research References

Papers and technical reports that informed the design of Logic-Lens's methodology,
risk taxonomy, scoring model, and tracing discipline. Each entry notes which part of
the tool it shaped.

---

## Semi-Formal Execution Tracing

**Abstract Interpretation: A Unified Lattice Model for Static Analysis of Programs
by Construction or Approximation of Fixpoints**
Cousot, P. & Cousot, R. (1977). *Proceedings of the 4th ACM Symposium on Principles
of Programming Languages (POPL)*, pp. 238–252.
https://doi.org/10.1145/512950.512973

The foundational framework for static program analysis. Establishes that any sound
approximation of program behavior can be expressed as a fixpoint over a lattice of
abstract values. Logic-Lens's Premises Construction — enumerating type contracts,
state preconditions, and name resolutions before tracing — is a lightweight instance
of this discipline: we fix an abstract domain (the four-section checklist) before
stepping through concrete execution paths.

---

**SLAM: A Static Driver Verifier**
Ball, T. & Rajamani, S. K. (2001). *Proceedings of the ACM SIGPLAN Conference on
Programming Language Design and Implementation (PLDI)*, pp. 1–11.
https://doi.org/10.1145/378795.378879

Introduced predicate abstraction + counterexample-guided abstraction refinement
(CEGAR) for automated driver verification. The key insight: when a forward trace
fails to establish a violation path, generate a counterexample and use it to
*refine the premises* rather than give up. Logic-Lens applies this idea in the
Backward Reasoning section of `semiformal-guide.md`: when forward tracing loses
the bug path, start from the confirmed failure point and trace backward to find
the broken premise.

---

**Precise Interprocedural Dataflow Analysis via Graph Reachability**
Reps, T., Horwitz, S. & Sagiv, M. (1995). *Proceedings of the 22nd ACM Symposium
on Principles of Programming Languages (POPL)*, pp. 49–61.
https://doi.org/10.1145/199448.199462

Defines the IFDS/IDE framework: context-sensitive interprocedural dataflow analysis
as a graph-reachability problem. Proves that tracking the full call stack (rather
than merging at join points) is necessary for precision. Logic-Lens implements this
principle via Call-Chain Context Labels in `semiformal-guide.md`: each trace step is
prefixed with the full `[caller → callee:line]` chain, preventing context collapse
across function boundaries and making cross-file findings unambiguous.

---

## Finding Quality and False-Positive Control

**A Few Billion Lines of Code Later: Using Static Analysis to Find Bugs in the
Real World**
Bessey, A., Block, K., Chelf, B., Chou, A., Fulton, B., Hallem, S., … Engler, D.
(2010). *Communications of the ACM*, 53(2), pp. 66–75.
https://doi.org/10.1145/1646353.1646374

Twenty-year retrospective on Coverity's deployment across thousands of codebases.
Central lesson: the value of a static analysis tool depends almost entirely on its
false-positive rate — developers stop reading reports if noise exceeds ~20%. Their
solution is confidence-tiered reporting: only emit findings when the checker has
high internal confidence; surface lower-confidence observations separately.

Logic-Lens maps this to the Confidence Rubric in `common.md` §7: High/Medium/Low
tiers with explicit trace requirements. Low-confidence findings are automatically
downgraded to Suggestion severity (−2 vs −15 deduction), preventing noisy Critical
alerts from burying the real bugs. The Logic Score deduction table (§6) is likewise
calibrated so that speculative divergences do not dominate the score.

---

## Concurrency Bug Taxonomy

**Learning from Mistakes: A Comprehensive Study of Real World Concurrency Bug
Characteristics**
Lu, S., Park, S., Seo, E. & Zhou, Y. (2008). *Proceedings of the 13th ACM
International Conference on Architectural Support for Programming Languages and
Operating Systems (ASPLOS)*, pp. 329–339.
https://doi.org/10.1145/1346281.1346323

Systematic study of 105 real concurrency bugs across MySQL, Apache httpd,
Mozilla Firefox, and OpenOffice. Key quantitative findings:
- ~68% of bugs are **Atomicity Violations (AV)**: a read-modify-write sequence
  that the programmer assumed atomic is interleaved by another thread.
- ~20% of bugs are **Order Violations (OV)**: an assumed execution order between
  two operations is not enforced by any synchronization primitive.
- The remaining ~12% are deadlocks and mixed patterns.

Logic-Lens incorporates this taxonomy into L7 (Concurrency / Async Hazard) in
`logic-risks.md` as two explicit subtypes with dedicated detection procedures. The
AV/OV classification helps reviewers identify the precise synchronization failure
rather than reporting a generic "race condition", and maps directly to the
remediation strategy (atomic wrapper vs. explicit ordering primitive).

---

## Code Review Process and Quality

**Expectations, Outcomes, and Challenges of Modern Code Review**
Bacchelli, A. & Bird, C. (2013). *Proceedings of the 35th International Conference
on Software Engineering (ICSE)*, pp. 712–721.
https://doi.org/10.1109/ICSE.2013.6606617

Large-scale study of code review at Microsoft. Counterintuitively, most review
comments are *not* about bugs — they are about code understanding, style, and design
alignment. Only ~15% of review comments find defects. This implies that a review
tool should explicitly separate logic-bug findings from style observations, or the
signal gets buried. Logic-Lens enforces this by requiring a full Premises → Trace →
Divergence chain before emitting any finding: style-level observations cannot satisfy
the trace requirement and fall out naturally.

---

**An Empirical Study of the Impact of Modern Code Review Practices on Software
Quality**
McIntosh, S., Kamei, Y., Adams, B. & Hassan, A. E. (2016). *Empirical Software
Engineering*, 21(5), pp. 2146–2189.
https://doi.org/10.1007/s10664-015-9381-9

Finds that *thorough* review (high reviewer participation, low patch churn after
review) is a significant predictor of lower post-release defect density, but
*perfunctory* review (rubber-stamping) has no measurable effect. Motivates
Logic-Lens's Scope Management rule (§9 of `common.md`): "A deep trace of 3 functions
beats pattern-matching across 30." Coverage breadth without trace depth produces
the same perfunctory outcome documented here.

---

## LLM Reasoning for Code Analysis

**Chain-of-Thought Prompting Elicits Reasoning in Large Language Models**
Wei, J., Wang, X., Schuurmans, D., Bosma, M., Ichter, B., Xia, F., … Zhou, D.
(2022). *Advances in Neural Information Processing Systems (NeurIPS)*, 35.
https://arxiv.org/abs/2201.11903

Demonstrates that prompting LLMs to produce intermediate reasoning steps
("chain-of-thought") substantially improves accuracy on multi-step reasoning tasks.
Logic-Lens's semi-formal tracing methodology is structurally equivalent to
chain-of-thought: the Premises → Trace → Divergence → Remedy sequence forces the
model to externalize its reasoning at each step, making it auditable and
substantially reducing hallucinated findings. The Iron Law ("NEVER emit a Remedy
before completing Premises → Trace → Divergence") is a direct operationalization of
the CoT discipline.

---

**SWE-bench: Can Language Models Resolve Real-World GitHub Issues?**
Jimenez, C., Yang, J., Wettig, A., Yao, S., Pei, K., Press, O. & Narasimhan, K.
(2024). *International Conference on Learning Representations (ICLR)*.
https://arxiv.org/abs/2310.06770

Benchmark of LLM performance on real GitHub issue resolution across 12 popular
Python repositories. Key finding: LLMs frequently identify the *symptom* site
correctly but produce fixes that address only the symptom, not the root cause —
a pattern the authors term "patch without understanding." This motivated the
Backward Reasoning section in `semiformal-guide.md`: starting from the confirmed
failure and tracing backward to the broken premise ensures the Remedy targets the
root cause, not just the manifestation.

---

## Bug Benchmarks Informing the Eval Suite

**Defects4J: A Database of Existing Faults to Enable Controlled Testing Studies
for Java Programs**
Just, R., Jalali, D. & Ernst, M. D. (2014). *Proceedings of the International
Symposium on Software Testing and Analysis (ISSTA)*, pp. 437–440.
https://doi.org/10.1145/2610384.2628055

Catalogue of 357 real, isolated Java bugs from Apache Commons Math, Joda-Time,
JFreeChart, Closure, and other widely-used libraries — each with the buggy and
fixed versions, the failing test, and the patch. Logic-Lens borrows the *style*
of these bugs (off-by-one in numerical libraries, DST handling in date
libraries, narrowing-cast overflows) for several `evals/v2/evals-v2.json` cases:
the `defects4j-style-commons-math-binarysearch-fix-all-L3-L6` case (id 285)
recreates the canonical lo+hi midpoint overflow alongside the lo=mid infinite
loop, both directly traceable to defects in Commons Math's history. The
`jodatime-style-dst-spring-forward-locate-L9` case (id 282) reproduces the
LocalDate-vs-ZonedDateTime hazard that motivated Joda-Time's eventual
deprecation in favor of `java.time` with explicit `getValidOffsets`.

---

**QuixBugs: A Multi-Lingual Program Repair Benchmark Set Based on the Quixey
Challenge**
Lin, D., Koppel, J., Chen, A. & Solar-Lezama, A. (2017). *Proceedings of the
Companion to the 2017 ACM SIGPLAN Conference on Systems, Programming,
Languages, and Applications: Software for Humanity (SPLASH)*, pp. 55–56.
https://doi.org/10.1145/3135932.3135941

40 single-line algorithmic bugs in 40 classic algorithms (mergesort, quicksort,
sieve, knapsack, …) with parallel Python and Java versions. Designed to test
program-repair tools on small, well-understood, deterministic faults. Logic-Lens
adapts this style for cases like `quixbugs-style-mergesort-merge-off-by-one-locate-L3`
(id 278) and `quixbugs-style-quicksort-aliased-input-mutation-L4` (id 279) —
familiar algorithms with a single subtle defect, ensuring the eval surface tests
the methodology on canonical CS-textbook material rather than only domain-specific
business logic.

---

**An Investigation of the Therac-25 Accidents**
Leveson, N. G. & Turner, C. S. (1993). *IEEE Computer*, 26(7), pp. 18–41.
https://doi.org/10.1109/MC.1993.274940

The definitive analysis of the Therac-25 radiation therapy machine that
delivered fatal overdoses to six patients between 1985 and 1987. The root cause
was a race condition between the operator console thread and the beam-control
thread on shared mode-and-filter flags — a textbook L7 atomicity-and-ordering
violation. Logic-Lens encodes this pattern in the
`therac25-style-race-mode-flag-L7-L4` case (id 280) so the eval suite tests
detection of safety-critical concurrency hazards, not just throughput-class
race conditions.

---

**ARIANE 5 Flight 501 Failure: Report by the Inquiry Board**
Lions, J. L. *et al.* (1996). European Space Agency.
http://sunnyday.mit.edu/nasa-class/Ariane5-report.html

The Ariane 5 launcher self-destructed 37 seconds after liftoff because a 64-bit
floating-point value (horizontal velocity from the inertial reference unit) was
silently narrowed to a 16-bit signed integer; the operand exceeded the range,
and the resulting Operand Error went unhandled. A single L2 (Type Contract
Breach) at a system boundary produced a $370M loss. Logic-Lens encodes this
pattern in `ariane5-style-narrowing-cast-overflow-locate-L2` (id 281) so the
eval suite explicitly probes for silent narrowing-cast hazards at boundaries
between languages or numeric domains.

---

## Architecture and Module Design

**On the Criteria To Be Used in Decomposing Systems into Modules**
Parnas, D. L. (1972). *Communications of the ACM*, 15(12), pp. 1053–1058.
https://doi.org/10.1145/361598.361623

Establishes information hiding as the primary criterion for module decomposition:
a module's interface should expose only what callers need, hiding the design
decisions likely to change. Directly informs L6 (Callee Contract Mismatch): when a
caller reaches into a callee's implementation rather than its documented interface,
it couples itself to a design decision the callee has the right to change. The L6
detection procedure (verify each caller assumption against the callee's actual
contract, not its name or intuition) is an application of Parnas's discipline.

---

**Out of the Tar Pit**
Moseley, B. & Marks, P. (2006). *BCS Software Practice Advancement (SPA)
Conference*.
https://curtclifton.net/papers/MoseleyMarks06a.pdf

Distinguishes essential complexity (inherent in the problem) from accidental
complexity (introduced by the solution). Argues that most software bugs are
caused by mutable state interacting with control flow — exactly the intersection
that L4 (State Mutation Hazard) and L5 (Control Flow Escape) target. The
Logic Score's higher deduction for Critical findings (−15) relative to Suggestions
(−2) reflects the authors' hierarchy: state/control bugs are more dangerous than
surface-level issues.
