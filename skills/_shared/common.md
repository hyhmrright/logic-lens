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

This framework uses three-step semi-formal execution tracing: **Premises → Trace → Divergence**. See `skills/_shared/semiformal-guide.md` for the full methodology, premises construction checklist, trace format, language-specific notes, and interprocedural reasoning guidance.

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

## When No Bugs Are Found

If the trace confirms no divergences, report Logic Score: 100 and state:
"No confirmed logic bugs found. All traced paths behave as specified."

Do not invent speculative findings to fill the Findings section. An empty Findings section with a high score is a valid, valuable result. If there are minor style or robustness suggestions, place them under 🟢 Suggestion with L-codes and a full Premises → Trace → Divergence → Remedy entry — never as prose observations outside the finding format.

---

## Scope Management

If the code under review exceeds ~150 lines or 5 non-trivial functions, do not attempt a superficial scan of everything. A deep trace of 3 functions is more valuable than shallow pattern-matching across 30.

Prioritize in this order:
1. Functions the user explicitly flagged as suspicious or recently broken — user-provided signals carry the highest information density.
2. Functions that touch external state, APIs, or user-controlled inputs.
3. Functions changed in the most recent commit (`git log --oneline -5 --name-only` if available).

State the covered scope at the top of the report. If you cannot cover everything, say so and explain the prioritization.

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

# Fix-all-specific config (only logic-fix-all reads this section;
# other skills ignore it).
fix_all:
  max_iterations: 3   # non-Critical iteration cap (Critical findings
                      # always loop until resolved; only
                      # Warning/Suggestion rounds count toward this cap)
```
