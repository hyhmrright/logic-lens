# Logic-Lens v0.5.0 — Outreach Pack & First Case Study

## TL;DR

No `SKILL.md` or guide changes in this release. v0.5.0 ships:

- **Three marketplace submission drafts** plus a marketplace research summary, including a critical finding that one of the marketplaces in the v0.4.3 outreach plan blocks `gh` CLI submissions.
- **First publishable case study** — a synthetic 8-file Python checkout module that intentionally embeds one canonical bug per L-code (L1–L6). Includes the full `/logic-health` output, a 2436-word walkthrough blog post, and reproduction instructions.
- **A documented negative result** for the v0.5.0 trigger-optimization pass — `run_loop.py` saturated at `recall=0%` across all six skills, so descriptions were not changed. Diagnosis and a methodology fix proposal for v0.6.x are checked in.

The descriptions kept from v0.4.x are still backed by 58/58 assertions on Opus 4.7 and Sonnet 4.6.

## What's new

### Outreach pack

- `docs/announcement/marketplace-pr-obra-superpowers-marketplace.md` — submission draft for the `obra/superpowers-marketplace` repo (879 stars, JSON registry pattern).
- `docs/announcement/marketplace-pr-helloianneo-awesome-claude-code-skills.md` — submission draft for the `helloianneo/awesome-claude-code-skills` repo (91 stars, README table pattern).
- `docs/announcement/marketplace-pr-hesreallyhim-awesome-claude-code.md` — submission draft for `hesreallyhim/awesome-claude-code`. **Operational warning embedded:** this repo blocks PRs and `gh` CLI submissions; submissions must be made via the browser issue form, otherwise the bot bans the account.
- `docs/announcement/marketplace-research-summary.md` — verified state of every marketplace target in the v0.4.3 outreach plan, with notes on the two placeholder repos that turned out not to exist (`davila7/claude-code-plugin-marketplace`, `Pi-Cla/awesome-claude-code-skills`).

### First case study

`docs/case-studies/01-checkout-module/` is a self-contained, reproducible demonstration of Logic-Lens on a single codebase. The codebase is synthetic but realistic: an 8-file Python checkout module where every file but two carries a canonical bug for one L-code.

```
docs/case-studies/01-checkout-module/
├── README.md                   reproduction steps
├── blog-post.md                2436-word walkthrough
├── logic-health-report.md      full /logic-health output (Score 52/100)
└── code/
    ├── cart.py                 L3 — boundary blindspot
    ├── pricing.py              L1 — shadow override
    ├── inventory.py            L4 — state mutation hazard
    ├── order.py                L2 — type contract breach
    ├── tax.py                  L6 — callee contract mismatch
    ├── payment.py              L5 — control flow escape
    ├── checkout.py             clean (control)
    └── notifications.py        clean (control)
```

You can clone the repo, run `/logic-health` on `code/`, and confirm the report.

### Negative result — `run_loop.py` saturates at recall=0%

We re-ran `scripts/run-trigger-evals.sh` on **all six** skills (the v0.4.3 release flagged this as the v0.5.0 target). Result, with `claude-sonnet-4-6` and 2 iterations per skill:

| Skill | Best score | Improvement |
|---|---|---|
| review | 4/8 (iter 1) | 0 |
| explain | 4/8 (iter 1) | 0 |
| diff | 4/8 (iter 1) | 0 |
| locate | 4/8 (iter 1) | 0 |
| health | 4/8 (iter 1) | 0 |
| fix-all | 4/8 (iter 1) † | 0 |

† `fix-all` iteration 2 aborted with an unrelated `SessionEnd` hook error from a third-party plugin (claude-mem); iteration 1 completed cleanly with the same recall=0% pattern as the other five skills.

Every iteration returned `precision=100%, recall=0%, accuracy=50%`. The metric saturated; the proposed rewritten descriptions provide no measured improvement, so they were **not adopted**.

Diagnosis (full version in `skills-workspace/v0.5.0-trigger-opt/FINDINGS.md`): the trigger judge in `run_loop.py` evaluates each description in isolation and tends to default to "no" on any prompt that could plausibly be served by general-purpose Claude. Without modeling the actual harness's multi-skill routing, the metric is uninformative for our skill family.

**v0.6.x will replace the trigger evaluator** with either a multi-skill judge context or instrumented harness runs against a hand-labeled prompt set. v0.4.x descriptions remain in place.

### Removed

- `skills-workspace/SESSION-STATUS.md` — a pre-v0.4.0 checkpoint that has been overtaken by four shipped releases. Removed to avoid misleading future readers.

## Verification

- `package.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `gemini-extension.json`, README badge — all bumped to `0.5.0`.
- 58/58 assertions from v0.4.0 / v0.4.1 still apply unchanged (no description changes).

## Breaking changes

None.

## Upgrade

```bash
/plugin update logic-lens
# or:
cd /path/to/logic-lens && git pull && bash hooks/session-start
```

🤖 Generated with [Claude Code](https://claude.com/claude-code)
