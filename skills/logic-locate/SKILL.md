---
name: logic-locate
description: >
  Fault localization that uses semi-formal execution tracing to pinpoint the
  specific code location responsible for a bug, test failure, crash, or
  wrong output — given a concrete failure to work from. Trigger this skill
  whenever a user has a specific, observable failure and wants to find where
  it comes from. Strong trigger phrases: "find the bug", "this test is
  failing", "track down this crash", "locate the error", "why is this test
  failing", "find the root cause", "help me debug this", "where is this
  coming from", "the error is somewhere in X — find it", or when the user
  provides a stack trace or failing assertion and asks what caused it. Also
  trigger when a user describes a specific observable symptom with enough
  detail to trace — e.g. "expected 70, got 100", "KeyError at line 89",
  "NoneType has no attribute X at services/foo.py:67", "cart empties when
  second tab opens". The key signal: there is a specific known failure
  (failing test, error message, wrong value, crash) — not just a suspicion
  that code might be wrong. Do NOT trigger for: general code review without
  a specific failure (use logic-review — the user says "check for bugs"
  but has no concrete failure yet), explaining what code does (use
  logic-explain), comparing two versions (use logic-diff), broad multi-module
  audits (use logic-health), vague questions like "what's wrong with my
  code in general", security or performance analysis, or refactoring requests.
---

# Logic-Lens — Fault Locate

## Setup
1. Read `../_shared/common.md` for the Iron Law and Report Template.
2. Read `../_shared/logic-risks.md` for L1–L6 risk codes; the fault will map to one of these.
3. Read `../_shared/semiformal-guide.md` for semi-formal tracing and interprocedural reasoning.
4. Read `logic-locate-guide.md` in this directory for the fault localization process.

## Process

**Scope:** The user must provide: (a) a failing test or error message, and (b) access to the relevant code. Ask for what's missing.

1. Understand the failure: what is the observed behavior, and what is the expected behavior? (Step 1 of the guide)
2. Identify the entry point closest to the failure: the test, the error site, or the reported symptom (Step 2)
3. Trace backward from the failure point, building premises at each step (Steps 3–4)
4. Follow interprocedural chains: when a callee's behavior is implicated, trace into it (Step 4b)
5. Identify the root divergence: the earliest point in the trace where the premise breaks (Step 5)
6. Classify the fault by L-code and output a focused report (Step 6)

**Mode line in report:** `Fault Locate`

**Output format:** Report focuses on the fault location, not a full codebase review. The Findings section contains a single Primary Fault (the root cause) and optionally Contributing Factors (conditions that enabled the fault). Logic Score is omitted — replace with **Fault Confidence:** High / Medium / Low based on trace completeness.
