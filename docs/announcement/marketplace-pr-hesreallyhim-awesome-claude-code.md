# PR Draft: hesreallyhim/awesome-claude-code

## Status

CONFIRMED EXISTS. Highly active — 1,600+ merged PRs, GitHub-actions bot merges approved submissions automatically.

## CRITICAL: No PR Submission

This repo does NOT accept PRs from contributors. All submissions must be made via the **GitHub Web UI issue form** at:

https://github.com/hesreallyhim/awesome-claude-code/issues/new?template=recommend-resource.yml

The `gh` CLI is explicitly blocked by the bot. The issue form must be filled out by a human in the browser.

---

## Issue Form Fill-Out Guide

Navigate to the URL above and fill each field as follows:

### Title (edit the placeholder)

```
[Resource]: Logic-Lens
```

### Category (dropdown)

Select: **Agent Skills**

### Sub-Category (dropdown)

Select: **General**

### Primary Link

```
https://github.com/hyhmrright/logic-lens
```

### Author Name

```
hyhmrright
```

### Author Link

```
https://github.com/hyhmrright
```

### License (dropdown)

Select: **MIT**

### Description

```
Logic-first code review plugin using semi-formal execution tracing. Surfaces behavioral bugs, type contract breaches, boundary blindspots, and interprocedural semantic mismatches — the logic errors that cause production incidents in code that passes all linters and type checks. Six slash-commands: /logic-review, /logic-explain, /logic-diff, /logic-locate, /logic-health, /logic-fix-all.
```

(Under 3 sentences, no emojis, not promotional, does not address the reader — matches list style.)

### Validate Claims (mandatory for plugins)

```
Clone https://github.com/hyhmrright/logic-lens and install the plugin: /plugin install logic-lens@hyhmrright/logic-lens. Open any non-trivial JavaScript or Python file in your project.
```

### Specific Task(s)

```
Ask Claude to review a function that has an off-by-one error, a null-path miss, or a boundary condition that linters would not catch.
```

### Specific Prompt(s)

```
/logic-review [paste the function here]

Then ask: "What risk codes did you assign and why?" The skill should return structured L1–L6 tagged findings with execution-trace justification rather than style comments.
```

### Additional Comments

```
Logic-Lens v0.5.0 release: https://github.com/hyhmrright/logic-lens/releases/tag/v0.5.0

The plugin ships with a structured risk taxonomy (L1–L6: Shadow Override, Type Contract Breach, Boundary Blindspot, State Mutation Hazard, Control Flow Escape, Callee Contract Mismatch) defined in skills/_shared/logic-risks.md, a semi-formal execution tracing methodology in skills/_shared/semiformal-guide.md, and six skills validated by 58/58 eval assertions on Opus 4.7 and Sonnet 4.6. It does not make any network calls except to the Anthropic API. No telemetry, no elevated permissions required.
```

### Checklist

Check all five boxes.

---

## Prerequisites / Gotchas

- **Must be >= 1 week old**: v0.5.0 released 2026-04-25; the repo's first public commit must be >= 1 week before submission. Verify with `gh api /repos/hyhmrright/logic-lens/commits?per_page=1&order=asc`.
- **No other open issues**: The form states "I do NOT have any other open issues in this repository." Confirm before submitting.
- **Maintainer is selective**: He explicitly states he cannot recommend every resource. The description and validation prompts must be crisp and evidence-based.
- **Bot validates format**: The bot auto-comments on formatting issues; these do not trigger the ban. Bans are for bypassing the form.
- **Spam deterrent**: Do not resubmit if the issue is closed — contact maintainer via Discussions instead.

---

## Maintainer Responsiveness Signal

- Merged PRs: ~1,660+ total (as of April 2026)
- Recent cadence: multiple merges per week (2026-04-21, 2026-04-15 x2, 2026-04-14 x2)
- Bot-automated: PRs are auto-created after maintainer approval — turnaround can be fast
- Maintainer login: `hesreallyhim`

---

## Post-Approval: Add Badge to README

Once accepted, add to `/Users/hyh/code/logic-lens/README.md`:

```markdown
[![Mentioned in Awesome Claude Code](https://awesome.re/mentioned-badge.svg)](https://github.com/hesreallyhim/awesome-claude-code)
```
