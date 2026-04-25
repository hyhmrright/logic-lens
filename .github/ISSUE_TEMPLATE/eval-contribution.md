---
name: New eval test case
about: Contribute a real bug example to the Logic-Lens benchmark suite
title: "[eval] <one-line bug description>"
labels: good first issue, eval
assignees: ''
---

## Bug category

Which Logic-Lens risk code does this bug fall under? (pick one)

- [ ] L1 — Shadow Override
- [ ] L2 — Type Contract Breach
- [ ] L3 — Boundary Blindspot
- [ ] L4 — State Mutation Hazard
- [ ] L5 — Control Flow Escape
- [ ] L6 — Callee Contract Mismatch

## Minimum reproducible code

Paste the smallest code snippet that contains the bug. Ideally two functions that interact — the bug should be invisible when looking at either function in isolation.

```
# paste code here
```

Language: <!-- python / js / go / rust / etc. -->

## Expected Logic-Lens output

What should Logic-Lens produce for this input? Fill in the four fields:

**Premises:**
<!-- What assumptions does the calling code make about the callee? -->

**Trace:**
<!-- Walk the execution path step by step until the bug manifests -->

**Divergence:**
<!-- The exact point where actual behavior departs from assumed behavior -->

**Remedy:**
<!-- Minimal fix -->

## Source

Where did this bug come from?

- [ ] I wrote it as a synthetic example
- [ ] Real PR / code review (no link needed, just confirm it's real)
- [ ] Production incident / postmortem
- [ ] Other: ___

## Notes

Any additional context — language quirks, framework behavior, why linters miss this.
