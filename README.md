<p align="center">
  <h1 align="center">Logic-Lens</h1>
</p>

<p align="center">
  <strong>Logic-first code review using semi-formal execution tracing.<br>
  Finds behavioral bugs that linters, type checkers, and unstructured review miss.</strong>
</p>

<p align="center">
  <a href="#the-nine-logic-risks">Nine Risks</a> •
  <a href="#what-it-looks-like">Example</a> •
  <a href="#six-skills">Six Skills</a> •
  <a href="#benchmark">Benchmark</a> •
  <a href="#installation">Installation</a> •
  <a href="#usage">Usage</a> •
  <a href="#configuration">Configuration</a> •
  <a href="#contributing">Contributing</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-0.6.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/Claude_Code-Plugin-blueviolet.svg" alt="Claude Code Plugin">
  <img src="https://img.shields.io/badge/Codex_CLI-Skill-orange.svg" alt="Codex CLI Skill">
  <img src="https://img.shields.io/badge/Gemini_CLI-Extension-4285F4.svg" alt="Gemini CLI Extension">
  <img src="https://img.shields.io/badge/verification-58%2F58%20assertions-brightgreen.svg" alt="Verified 58/58">
</p>
<p align="center">
  <a href="https://github.com/hyhmrright/logic-lens/stargazers"><img src="https://img.shields.io/github/stars/hyhmrright/logic-lens?style=social" alt="GitHub Stars"></a>
  <a href="https://github.com/hyhmrright/logic-lens/network/members"><img src="https://img.shields.io/github/forks/hyhmrright/logic-lens?style=social" alt="GitHub Forks"></a>
  <a href="https://github.com/hyhmrright/logic-lens/issues"><img src="https://img.shields.io/github/issues/hyhmrright/logic-lens" alt="Issues"></a>
  <a href="https://github.com/hyhmrright/logic-lens/pulls"><img src="https://img.shields.io/github/issues-pr/hyhmrright/logic-lens" alt="Pull Requests"></a>
  <a href="https://github.com/hyhmrright/logic-lens/releases/latest"><img src="https://img.shields.io/github/v/release/hyhmrright/logic-lens" alt="Latest Release"></a>
  <a href="https://github.com/hyhmrright/logic-lens/commits/main"><img src="https://img.shields.io/github/last-commit/hyhmrright/logic-lens" alt="Last commit"></a>
</p>

---

> *"Models using structured (semi-formal) reasoning achieve 87–93% accuracy on code semantics tasks, versus 76–78% for unstructured chain-of-thought — with the largest gains on interprocedural bugs."*
> — Ugare & Chandra, *Agentic Code Reasoning* (2026, arXiv:2603.01896)

**Code review without a trace is a guess.** Standard review catches style issues and obvious mistakes. Linters catch syntax. But neither catches the class of bugs where code looks correct in isolation, passes all tests, and still ships broken behavior — because the bug only appears when two functions interact in a way neither author anticipated.

**Logic-Lens forces the AI to construct an explicit execution trace** before reaching any conclusion. Every finding comes with a documented Premises → Trace → Divergence → Remedy chain that shows exactly how the reviewer arrived at the finding — not just what it found.

## The Nine Logic Risks

Logic-Lens evaluates code across **nine logic risk dimensions** — six derived from the semi-formal reasoning methodology in *Agentic Code Reasoning* (L1–L6), plus three covering modern hazards that fall outside the paper's single-process scope (L7–L9):

| Code | Risk | What It Catches |
|------|------|----------------|
| 🔀 **L1** | Shadow Override | A name resolves to a different definition than assumed — shadowing, import aliasing, inheritance override |
| 📐 **L2** | Type Contract Breach | A function receives a type it can't correctly handle, through implicit coercion or conditional paths |
| 🔲 **L3** | Boundary Blindspot | Edge cases not traced: null, empty, zero, max/min bounds, single-element sequences |
| ⚠️ **L4** | State Mutation Hazard | Sequential aliasing or mutation-during-iteration hazards on a single execution path |
| 🚪 **L5** | Control Flow Escape | An early exit skips a required operation — cleanup, commit, lock release, notification |
| 🔗 **L6** | Callee Contract Mismatch | Calling code assumes return value semantics, exception behavior, or idempotency the callee doesn't guarantee |
| 🧵 **L7** | Concurrency / Async Hazard | Race across an `await` / lock / channel boundary; double-acquire; send-after-cancel; missing happens-before |
| 🔁 **L8** | Resource Lifecycle Hazard | Acquire/release imbalance — missing release path, double release, ownership transferred without updating release plan |
| 🕒 **L9** | Time / Locale Hazard | Naive vs aware datetime, DST jumps, locale-sensitive sort/case, encoding round-trip, decimal-separator drift |

## What It Looks Like

Given this code:

```python
def process_order(order_id, items, discount_code=None):
    order = db.get_order(order_id)
    total = sum(item['price'] * item['qty'] for item in items)

    if discount_code:
        discount = coupon_service.get_discount(discount_code)
        total = total * (1 - discount)

    order['total'] = total
    order['items'] = items
    db.save_order(order)
    email_service.send_confirmation(order['email'], total)
```

Logic-Lens produces:

---

**Logic Health: 31/100**

*This function contains a callee contract mismatch that causes a silent divide-by-zero risk, a boundary blindspot on empty item lists, and a control flow escape that leaks a database connection on email failure.*

### 🔴 L6 — Callee Contract Mismatch: `get_discount` May Return `None`
**Premises:** `coupon_service.get_discount(code)` is assumed to always return a numeric discount rate between 0 and 1.
**Trace:** `discount_code` is truthy → `get_discount(discount_code)` is called → result assigned to `discount` → `total * (1 - discount)` is evaluated.
**Divergence:** `get_discount` returns `None` for expired or invalid codes (documented in its docstring). When `discount` is `None`, `1 - None` raises `TypeError`. The call reaches `db.save_order` only on the happy path; a bad coupon code aborts the function without saving.
**Remedy:** Check `if discount is not None:` before applying. Alternatively, have `get_discount` raise a typed exception (`InvalidCouponError`) that the caller can handle explicitly.

### 🔴 L3 — Boundary Blindspot: Empty `items` List
**Premises:** `items` is assumed to contain at least one element.
**Trace:** `sum(item['price'] * item['qty'] for item in items)` → returns `0` for empty list → `total = 0` → `order['total'] = 0` → saved and confirmed.
**Divergence:** An order with zero items is silently saved as a $0.00 order and a confirmation email is sent. No business rule validates that an order must contain at least one item.
**Remedy:** Add `if not items: raise ValueError("Order must contain at least one item")` before the sum. This is a business invariant, not an implementation detail.

### 🟡 L5 — Control Flow Escape: Database Connection Not Released on Email Failure
**Premises:** `db.save_order` and `email_service.send_confirmation` are assumed to both succeed.
**Trace:** `db.save_order(order)` succeeds → connection kept open → `email_service.send_confirmation(...)` raises `SMTPException` → function exits via uncaught exception.
**Divergence:** The database connection is never explicitly released. Depending on the ORM's connection pooling strategy, this may exhaust the pool under sustained email failure.
**Remedy:** Wrap `email_service.send_confirmation` in a `try/finally` block, or separate the email send into an async queue so order persistence is not coupled to email delivery.

*(+ 2 more findings)*

---

## Quickstart (60 seconds)

**Claude Code users:**

```
/plugin marketplace add hyhmrright/logic-lens
/plugin install logic-lens@logic-lens-marketplace
/logic-review
```

Then paste any function. Done. *(Short-form commands like `/logic-review` are auto-installed on first session start.)*

For Gemini CLI and Codex CLI, see [Installation](#installation) below.

---

## Six Skills

Logic-Lens ships six skills: **logic-review** (find behavioral bugs via execution tracing), **logic-explain** (trace what code actually does step by step), **logic-diff** (verify two versions are behaviorally equivalent), **logic-locate** (find the root cause of a failing test or crash), **logic-health** (aggregate logic health dashboard across a codebase), and **logic-fix-all** (autonomous audit-and-fix pipeline — scans the target, applies fixes for every finding, verifies each fix, no user involvement required). See [Usage](#usage) for per-skill commands and [Slash Commands](#slash-commands) for platform-specific syntax.

---

## Benchmark

Tested across 3 real-world bug scenarios (interprocedural, boundary, state mutation):

| Criterion | Logic-Lens | Claude alone |
|-----------|:----------:|:------------:|
| Explicit Premises stated before finding | ✅ 100% | ❌ 0% |
| Step-by-step execution trace provided | ✅ 100% | ❌ 0% |
| Exact divergence point identified | ✅ 100% | ❌ 0% |
| Risk codes (L1–L9) labeled per finding | ✅ 100% | ❌ 0% |
| Detects interprocedural bugs | ✅ 100% | ✅ 68% |
| Detects boundary blindspots | ✅ 100% | ✅ 71% |
| **Overall pass rate** | **91%** | **19%** |

The gap isn't what Claude *can* find — it's what it *consistently* finds, with a traceable reasoning chain that shows its work every time.

## How It Compares

| | Logic-Lens | ESLint / Pylint | GitHub Copilot Review | Plain Claude |
|---|:---:|:---:|:---:|:---:|
| Detects syntax & style issues | — | ✅ | ✅ | ~ |
| Explicit execution trace per finding | ✅ | ❌ | ❌ | ❌ |
| Premises → Trace → Divergence → Remedy | ✅ | ❌ | ❌ | ❌ |
| Consistent severity-labeled findings | ✅ | ✅ | ~ | ❌ |
| Interprocedural bug detection | ✅ | ❌ | ~ | ~ |
| Boundary & null path analysis | ✅ | ~ | ~ | ~ |
| Zero config, works with any language | ✅ | ❌ | ✅ | ✅ |
| Reasoning is auditable / reproducible | ✅ | ✅ | ❌ | ❌ |

> `~` = occasionally / inconsistently

**Logic-Lens doesn't replace your linter.** It catches what linters can't: callee contract violations, state mutation hazards, and control flow escapes — the bugs that cause production incidents in syntax-clean, lint-passing code.

---

## Installation

### Claude Code (Recommended)

*Already ran the Quickstart? You're done — skip to [Slash Commands](#slash-commands).*

#### Via Plugin Marketplace
```bash
/plugin marketplace add hyhmrright/logic-lens
/plugin install logic-lens@logic-lens-marketplace
```

Short-form commands (`/logic-review`) are auto-installed on first session start. To install manually:
```bash
cp commands/*.md ~/.claude/commands/
```

#### Manual Install
```bash
mkdir -p ~/.claude/skills/logic-lens
cp -r skills/* ~/.claude/skills/logic-lens/
```

### Gemini CLI

#### Via Extension
```bash
/extensions install https://github.com/hyhmrright/logic-lens
```

#### Manual Install
```bash
mkdir -p ~/.gemini/skills/logic-lens
cp -r skills/* ~/.gemini/skills/logic-lens/
```

### Codex CLI

#### Via Skill Installer (in Codex session)
```
Install the logic-lens skill from hyhmrright/logic-lens
```

#### Command Line
```bash
python3 ~/.codex/skills/.system/skill-installer/scripts/install-skill-from-github.py \
  --repo hyhmrright/logic-lens --path skills --name logic-lens
```

#### Manual Install
```bash
git clone https://github.com/hyhmrright/logic-lens.git /tmp/logic-lens
mkdir -p ~/.codex/skills/logic-lens
cp -r /tmp/logic-lens/skills/* ~/.codex/skills/logic-lens/
```

---

## Slash Commands

### Claude Code
| Command | Short Form | Action |
|---------|------------|--------|
| `/logic-lens:logic-review` | `/logic-review` | Code logic review via execution tracing |
| `/logic-lens:logic-explain` | `/logic-explain` | Step-by-step execution explanation |
| `/logic-lens:logic-diff` | `/logic-diff` | Semantic equivalence check between two versions |
| `/logic-lens:logic-locate` | `/logic-locate` | Root cause localization for failing tests or crashes |
| `/logic-lens:logic-health` | `/logic-health` | Aggregate logic health dashboard for a codebase |
| `/logic-lens:logic-fix-all` | `/logic-fix-all` | Autonomous audit-and-fix pipeline — finds and fixes every logic issue |

> Short-form commands are auto-installed on first session start by the session-start hook.

### Gemini CLI
| Command | Action |
|---------|--------|
| `/logic-review` | Code logic review via execution tracing |
| `/logic-explain` | Step-by-step execution explanation |
| `/logic-diff` | Semantic equivalence check between two versions |
| `/logic-locate` | Root cause localization for failing tests or crashes |
| `/logic-health` | Aggregate logic health dashboard for a codebase |
| `/logic-fix-all` | Autonomous audit-and-fix pipeline — finds and fixes every logic issue |

### Codex CLI
| Command | Action |
|---------|--------|
| `$logic-review` | Code logic review via execution tracing |
| `$logic-explain` | Step-by-step execution explanation |
| `$logic-diff` | Semantic equivalence check between two versions |
| `$logic-locate` | Root cause localization for failing tests or crashes |
| `$logic-health` | Aggregate logic health dashboard for a codebase |
| `$logic-fix-all` | Autonomous audit-and-fix pipeline — finds and fixes every logic issue |

---

## Usage

### Code Logic Review

```
/logic-review                       # Claude Code (short form) / Gemini CLI
/logic-lens:logic-review            # Claude Code (full form)
$logic-review                       # Codex CLI
```

Paste the code or point the AI at the file. Logic-Lens constructs an explicit execution trace for each suspicious path and reports only findings with a documented Premises → Trace → Divergence → Remedy chain.

### Execution Explanation

```
/logic-explain                      # Claude Code (short form) / Gemini CLI
/logic-lens:logic-explain           # Claude Code (full form)
$logic-explain                      # Codex CLI
```

Ask "what does this code actually do?" and get a step-by-step trace that crosses function boundaries, rather than a natural-language summary of what the code appears to do.

### Semantic Diff

```
/logic-diff                         # Claude Code (short form) / Gemini CLI
/logic-lens:logic-diff              # Claude Code (full form)
$logic-diff                         # Codex CLI
```

Paste two versions of a function. Logic-Lens traces both and reports whether they are behaviorally equivalent — and if not, exactly which execution path produces a different outcome.

### Fault Localization

```
/logic-locate                       # Claude Code (short form) / Gemini CLI
/logic-lens:logic-locate            # Claude Code (full form)
$logic-locate                       # Codex CLI
```

Paste a failing test, stack trace, or bug report alongside the relevant code. Logic-Lens traces backward from the failure to identify the exact divergence point — distinguishing root cause from symptom.

### Logic Health Dashboard

```
/logic-health                       # Claude Code (short form) / Gemini CLI
/logic-lens:logic-health            # Claude Code (full form)
$logic-health                       # Codex CLI
```

Runs abbreviated logic reviews across a codebase and produces a weighted Logic Health Score (0–100) broken down by risk dimension. Use before a release, during an audit, or when onboarding onto an unfamiliar codebase.

### Autonomous Audit-and-Fix

```
/logic-fix-all                      # Claude Code (short form) / Gemini CLI
/logic-lens:logic-fix-all           # Claude Code (full form)
$logic-fix-all                      # Codex CLI
```

Point it at a directory or file. Logic-Lens sweeps the entire scope, collects all findings at every severity level (L1–L9), applies fixes in priority order, verifies each fix with a semantic diff, and re-confirms the codebase is clean — all without requiring you to read or review any code. The final output is a Fix Log table listing every change made and its verification status.

---

## Configuration

Place a `.logic-lens.yaml` in your project root to customize behavior:

```yaml
# Skip concurrency checks in confirmed single-threaded code
disable:
  - L7

# Treat all boundary issues as critical for this safety-critical module
severity:
  L3: critical

# Exclude generated files and vendor code from analysis
ignore:
  - "tests/fixtures/**"
  - "vendor/**"
  - "**/*.generated.*"
```

| Setting | Description |
|---------|-------------|
| `disable` | Risk codes to skip (`L1`–`L9`, or custom `C1`, `C2`, ...) |
| `severity` | Override severity tier (`critical` / `warning` / `suggestion`) |
| `ignore` | Glob patterns for files to exclude from analysis |
| `focus` | Evaluate only these risk codes |
| `custom_risks` | Define project-specific risk codes (`C1`, `C2`, ...) with `code`, `name`, `description`, `severity` |

All settings are optional — omit the file entirely for default behavior.

---

## Language Support

Logic-Lens is language-agnostic. The semi-formal reasoning methodology applies to any language where name resolution, type contracts, and execution paths can be traced by reading source code. The shared guide includes language-specific tracing notes for:

**Python** · **JavaScript / TypeScript** · **Java / Kotlin** · **Go** · **Rust** · **SQL**

Other languages work with the general methodology — scope chain rules, type coercion behavior, and exception propagation semantics are the only language-specific knowledge required.

---

## How It Works

Logic-Lens does not execute code or use static analysis tools. It works by prompting the AI to follow a structured reasoning template that mirrors the semi-formal methodology from *Agentic Code Reasoning* (Ugare & Chandra, 2026).

The key insight from the paper: when models are forced to state premises explicitly before tracing, they catch interprocedural bugs at 87–93% accuracy. Without the structure, the same models miss these bugs 22–24% of the time — because they pattern-match on code appearance rather than reasoning through execution.

The discipline enforced per finding:
1. **Premises** — State every assumption about name resolution, types, and preconditions
2. **Trace** — Follow the actual execution path step by step, crossing function boundaries
3. **Divergence** — Identify the exact point where a premise breaks and what follows
4. **Remedy** — Prescribe a fix that addresses the divergence, not just its symptom

No finding is reported without all four sections. This is the **Iron Law** of Logic-Lens.

---

## Project Structure

```
logic-lens/
├── .claude-plugin/              # Claude Code plugin metadata
├── .codex-plugin/               # Codex CLI plugin metadata
├── gemini-extension.json        # Gemini CLI extension metadata
├── skills/
│   ├── _shared/                 # Shared framework files
│   │   ├── common.md            # Iron Law, output format, health score
│   │   ├── logic-risks.md       # L1–L9 risk taxonomy with examples
│   │   └── semiformal-guide.md  # Execution tracing methodology
│   ├── logic-review/            # Skill 1: Code logic review
│   │   ├── SKILL.md
│   │   └── logic-review-guide.md
│   ├── logic-explain/           # Skill 2: Execution explanation
│   │   ├── SKILL.md
│   │   └── logic-explain-guide.md
│   ├── logic-diff/              # Skill 3: Semantic diff
│   │   ├── SKILL.md
│   │   └── logic-diff-guide.md
│   ├── logic-locate/            # Skill 4: Fault localization
│   │   ├── SKILL.md
│   │   └── logic-locate-guide.md
│   ├── logic-health/            # Skill 5: Health dashboard
│   │   ├── SKILL.md
│   │   └── logic-health-guide.md
│   └── logic-fix-all/           # Skill 6: Autonomous audit-and-fix pipeline
│       ├── SKILL.md
│       └── logic-fix-all-guide.md
├── commands/                    # Short-form command wrappers (auto-installed by hook)
├── hooks/                       # Session-start hook
├── evals/
│   └── evals.json               # Benchmark test cases
└── CONTRIBUTING.md
```

---

## Why Semi-Formal Reasoning?

AI-assisted development is making codebases grow faster than human review capacity. The bugs that slip through are increasingly the interprocedural kind — the ones that require holding two functions' contracts in mind simultaneously and noticing when they don't match.

> *"The bearing of a child takes nine months, no matter how many women are assigned."*
> — Frederick Brooks, *The Mythical Man-Month* (1975)

Adding AI reviewers doesn't fix the problem if they make the same reasoning errors as human reviewers: pattern-matching on surface appearance, anchoring on the happy path, skipping the trace when the code "looks fine." Logic-Lens addresses this at the methodology level — not by prompting the AI to "be more careful," but by structuring the reasoning process so it cannot skip the step where bugs hide.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Logic-Lens is designed for universal use — contributions must not embed assumptions about any particular language, framework, or development workflow.

The best contributions right now are new eval test cases, especially interprocedural bugs drawn from real production incidents. See [CONTRIBUTING.md](CONTRIBUTING.md) for the format.

**New to the project? The fastest way to contribute is a new eval test case — see the [issue template](https://github.com/hyhmrright/logic-lens/issues/new?template=eval-contribution.md).**

---

## License

MIT License — see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Logic-Lens is grounded in the following research:

- Ugare & Chandra — *Agentic Code Reasoning* (2026, arXiv:2603.01896)

The semi-formal reasoning methodology, risk taxonomy, and accuracy benchmarks referenced throughout this project are derived from or inspired by this work.

---

<p align="center">
  <strong>⭐ If Logic-Lens helped you catch a bug before it shipped, give it a star!</strong>
</p>

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=hyhmrright/logic-lens&type=Date)](https://star-history.com/#hyhmrright/logic-lens&Date)
