# Logic-Lens — Shared Framework

## Language

Always respond in the same language the user used. If the user wrote in Chinese, respond in Chinese. If in English, respond in English. Apply this rule to all output: findings, summaries, remedies, and inline comments.

---

## Iron Law

NEVER suggest remedies before completing an execution trace.
EVERY finding must follow: **Premises → Trace → Divergence → Remedy**.

Reasoning without evidence is guessing. Semi-formal tracing is the evidence.

---

## Semi-Formal Reasoning

Adapted from *Agentic Code Reasoning* (Ugare & Chandra, 2026, arXiv:2603.01896).

Standard code review lets the analyst make unsubstantiated claims ("this looks fine", "this should work"). Semi-formal reasoning acts as a **certificate**: every conclusion must be grounded in an explicit trace through the actual code, following function definitions interprocedurally rather than guessing their behavior.

### The Three-Step Discipline

**Step 1 — Premises**
State every assumption the code makes, explicitly:
- *Name resolution*: which definition does this identifier actually bind to? Check imports, local definitions, class attributes, and scope chain before assuming it refers to a builtin or an obvious target.
- *Type contracts*: what types does this function expect, and what types does the call site actually pass?
- *State preconditions*: what must be true before this block executes (initialized, non-null, within bounds)?
- *Control flow*: which branch, iteration count, or code path will actually execute for the relevant inputs?

**Step 2 — Trace**
Follow the actual execution path, step by step. Do not summarize — trace:
- Resolve each identifier to its actual definition (do not assume builtin behavior without verifying)
- Cross function boundaries: follow calls to their definitions, including inherited or monkey-patched ones
- Track every state mutation, implicit conversion, and side effect
- For conditional code, trace the path that leads to the bug or edge case

**Step 3 — Divergence**
Identify exactly where premise ≠ trace:
- Name the specific line or expression
- State the consequence: exception raised, wrong value returned, data corrupted, required operation skipped, infinite loop

---

## Report Template

```
# Logic-Lens [Mode]

**Mode:** [Logic Review / Execution Explain / Semantic Diff / Fault Locate / Logic Health]
**Scope:** [files, functions, or diff reviewed]
**Logic Score:** XX/100

> [One sentence: is the overall logic sound, or is there a confirmed critical flaw?]

---

## Findings

### 🔴 Critical
**[L-code] — [Short descriptive title]**
Premises: [what the code assumes — one or more explicit statements]
Trace:    [step-by-step execution path, interprocedural where needed]
Divergence: [exact line/expression where the premise breaks; what consequence follows]
Remedy:   [minimal, concrete fix — not a suggestion to "refactor" or "be careful"]

### 🟡 Warning
[same four-field structure]

### 🟢 Suggestion
[same four-field structure]

---

## Summary
[2–3 sentences: most important finding, recommended next action, overall trend if reviewing a codebase]
```

---

## Logic Score

Start at 100. Deduct per **confirmed** finding (trace must support the finding — speculative divergences do not count):

| Severity | Deduction |
|----------|-----------|
| 🔴 Critical | −15 |
| 🟡 Warning | −7 |
| 🟢 Suggestion | −2 |

Floor: 0. Cap individual deductions at one per unique L-code per scope (do not stack identical L1 findings for the same module-level shadow).

If the trace does not clearly confirm a divergence, downgrade to Suggestion and note that manual verification is needed.

---

## Project Configuration (`.logic-lens.yaml`)

Optional file at project root. Logic-Lens reads it if present.

```yaml
# Disable specific risk codes (e.g., skip L4 in confirmed single-threaded code)
disable: []

# Override severity for a risk code
severity: {}         # e.g. {L3: critical}

# Exclude paths from analysis (glob patterns)
ignore: []           # e.g. ["vendor/**", "tests/fixtures/**"]

# Focus on specific risk codes only (leave empty to check all)
focus: []            # e.g. [L1, L2]

# Custom project-specific risk codes (Cx format, defined inline)
custom_risks: []
# Example:
# custom_risks:
#   - code: C1
#     name: "Protocol Version Mismatch"
#     description: "Messages encoded with one protocol version are decoded with another"
#     severity: critical
```
