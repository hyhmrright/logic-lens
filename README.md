# Logic-Lens

**Logic-first code review using semi-formal execution tracing.**

Logic-Lens surfaces behavioral bugs, type contract breaches, boundary blindspots, and interprocedural semantic mismatches — the logic errors that cause test failures and production incidents after syntax-clean code ships. It works by forcing the AI to construct an explicit execution trace rather than guess at code behavior.

> Based on *Agentic Code Reasoning* (Ugare & Chandra, 2026, arXiv:2603.01896).

---

## The Problem

Standard code review catches style issues and obvious mistakes. Linters catch syntax. But neither catches the class of bugs where:

- Code looks correct in isolation but calls the wrong function due to name shadowing
- A function assumes a callee returns a non-null value, but it doesn't under specific conditions
- A refactor is semantically correct for the common case but breaks an edge case
- A bug only appears when two functions interact in a way neither author anticipated

These are **logic bugs** — and they require tracing actual execution paths to find.

## The Solution: Semi-Formal Reasoning

Logic-Lens applies a three-step discipline to every analysis:

1. **Premises** — State all assumptions explicitly (name resolution, type contracts, state preconditions)
2. **Trace** — Follow the actual execution path step-by-step, crossing function boundaries
3. **Divergence** — Identify exactly where the premise breaks and what consequence follows

Every finding follows: **Premises → Trace → Divergence → Remedy**

This structured approach prevents the "it looks fine" failure mode of unstructured review and consistently surfaces bugs that require interprocedural reasoning to discover.

---

## Five Skills

| Command | What It Does |
|---------|-------------|
| `/logic-review` | Code logic review — find behavioral bugs via execution tracing |
| `/logic-explain` | Execution explanation — trace what code actually does, step by step |
| `/logic-diff` | Semantic diff — verify two code versions are behaviorally equivalent |
| `/logic-locate` | Fault localization — find the root cause of a failing test or crash |
| `/logic-health` | Logic health dashboard — aggregate logic review across a codebase |

---

## Six Logic Risk Codes

| Code | Name | What It Catches |
|------|------|----------------|
| L1 | Shadow Override | A name resolves to a different definition than assumed (shadowing) |
| L2 | Type Contract Breach | A function receives a type it can't correctly handle |
| L3 | Boundary Blindspot | Edge cases not traced: null, empty, zero, max/min bounds |
| L4 | State Mutation Hazard | Shared mutable state read/written in incorrect order |
| L5 | Control Flow Escape | Early exit skips a required operation (cleanup, commit, notification) |
| L6 | Callee Contract Mismatch | Calling code assumes behavior the callee doesn't guarantee |

---

## Installation

### Claude Code

```bash
claude mcp install https://github.com/your-org/logic-lens
```

Or clone and install locally:
```bash
git clone https://github.com/your-org/logic-lens ~/.claude/plugins/logic-lens
```

Skills are available as `/logic-review`, `/logic-explain`, etc.

### Codex CLI

```bash
codex plugin install https://github.com/your-org/logic-lens
```

Skills are available as `$logic-review`, `$logic-explain`, etc.

### Gemini CLI

```bash
gemini extension install https://github.com/your-org/logic-lens
```

Skills are available as `/logic-review`, `/logic-explain`, etc.

---

## Project Configuration

Create `.logic-lens.yaml` at your project root to customize behavior:

```yaml
# Skip concurrency checks in confirmed single-threaded code
disable: [L4]

# Treat all boundary issues as critical for this safety-critical module
severity:
  L3: critical

# Exclude test fixtures from analysis
ignore:
  - "tests/fixtures/**"
  - "vendor/**"
```

---

## Language Support

Logic-Lens is language-agnostic. The semi-formal reasoning methodology applies to any language where name resolution, type contracts, and execution paths can be traced by reading source code. The shared guide includes language-specific tracing notes for:

Python · JavaScript / TypeScript · Java / Kotlin · Go · Rust · SQL

Other languages work with the general methodology.

---

## How It Works

Logic-Lens does not execute code or use static analysis tools. It works by prompting the AI to apply structured reasoning templates that mirror the semi-formal methodology from the research paper. The key insight from the paper: models using structured (semi-formal) reasoning achieve 87–93% accuracy on code semantics tasks, versus 76–78% for unstructured chain-of-thought — with the largest gains on interprocedural bugs that require following function calls rather than guessing their behavior.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Logic-Lens is designed for universal use — contributions must not embed assumptions about any particular language, framework, or development workflow.

---

## License

MIT
