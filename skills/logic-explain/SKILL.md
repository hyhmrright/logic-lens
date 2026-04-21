---
name: logic-explain
description: >
  Execution path explanation that traces through code step by step to reveal
  what the code actually does — not what it appears to do. Trigger this
  skill whenever a user wants to understand runtime behavior, trace a specific
  execution scenario, or learn why code produces unexpected output. Strong
  trigger phrases: "walk me through this", "trace this for me", "what
  actually happens when I call X", "follow the execution", "explain what
  this does step by step", "why does this print/return X instead of Y",
  "I don't understand what this code does", "trace through X with input Y",
  "what happens internally when", "explain the execution path". Also trigger
  when a user shares code and asks why it behaves a certain way, even if
  they don't use the word "trace" — e.g. "why does this print [3,3,3]
  instead of [0,1,2]", "what does yield from actually do here", "how does
  this async code execute". Do NOT trigger for: finding bugs in code without
  a specific behavioral question (use logic-review), checking if two code
  versions are equivalent (use logic-diff), locating the root cause of a
  failing test (use logic-locate), broad multi-module audits (use
  logic-health), general concept explanations not tied to specific code
  ("explain closures in general"), architecture or design questions, or
  performance/security analysis.
---

# Logic-Lens — Execution Explain

## Setup
1. Read `../_shared/common.md` for the Iron Law and Report Template.
2. Read `../_shared/semiformal-guide.md` for the full semi-formal tracing methodology.
3. Read `logic-explain-guide.md` in this directory for the explanation process.

## Process

**Scope:** Ask the user which function or code path to explain, and which input scenario to trace (if none specified, use the most common/interesting case).

1. State the entry point and the scenario being traced (Step 1 of the guide)
2. Build premises: resolve all names, types, and preconditions before starting the trace (Step 2)
3. Produce the step-by-step execution trace, crossing function boundaries where relevant (Step 3)
4. Highlight any surprising or non-obvious behavior discovered during the trace (Step 4)
5. Summarize what the code actually does vs. what a casual reader might assume (Step 5)

**Mode line in report:** `Execution Explain`

**Note:** Execution Explain does not compute a Logic Score — it is descriptive, not evaluative. Omit the score line from the report header.
