# Contributing to Logic-Lens

## What We're Building

Logic-Lens is a language-agnostic, platform-universal code logic review toolkit grounded in
semi-formal execution tracing (arXiv:2603.01896). The goal is to surface behavioral bugs
that syntax checkers, linters, and surface-level code review miss — by forcing the reviewer
to construct explicit execution traces rather than relying on intuition.

## Ground Rules

1. **No personal conventions.** Logic-Lens is designed for universal use across languages,
   teams, and codebases. Contributions must not embed assumptions about any particular
   language ecosystem, framework, or development workflow.

2. **The Iron Law is inviolable** (canonical definition in `skills/_shared/common.md`). Changes that weaken this requirement will not be accepted.

3. **Grounded in the paper.** New risk codes, methodology changes, or guide additions
   should be traceable to either the semi-formal reasoning paper (arXiv:2603.01896) or
   a well-documented pattern of interprocedural bugs in real codebases.

4. **Language-agnostic by default.** Examples in guide files should cover multiple
   languages. If a risk code only manifests in one language, note that explicitly —
   but design the detection methodology to generalize.

## Adding a Risk Code

New built-in risk codes (the next available is **L10**) require:
1. A clear definition of what the code covers that does not overlap with L1–L9.
2. A detection methodology using semi-formal tracing.
3. Examples in at least two different languages.
4. A severity assessment rationale.
5. At least 2 eval cases in `evals/content/v2/evals-v2.json`.

## Adding a Skill

New skills (beyond the six built-in skills) require:
1. A SKILL.md with a clear "Do NOT trigger for:" clause.
2. A guide file with numbered steps explaining the *why* behind each step.
3. A command wrapper in `commands/`.
4. The skill name added to the `for skill in ...` loop in `hooks/session-start`.
5. At least 3 eval cases in `evals/content/v2/evals-v2.json`.

No registration is needed in `gemini-extension.json` or `.codex-plugin/plugin.json` — both
discover skills by scanning the `skills/` directory. See CLAUDE.md → "Adding a New Skill" for
the full checklist.

## Eval Cases

Eval cases in `evals/content/v2/evals-v2.json` must include code snippets that a reviewer could
evaluate without running the code. The `expected_output` should describe what a
correct Logic-Lens analysis would find — not what the correct fix is. Trigger evals
(per-skill activation tests) live in `evals/trigger/v2/trigger-evals-*.json`.

## Version Bumping

Run `npm run bump-version -- <x.y.z>` — it rewrites all six manifests and the README badge at
once, then validates consistency. Add the `CHANGELOG.md` entry by hand; the script does not
touch it.

Use semantic versioning: patch for guide improvements, minor for new skills or risk codes, major for methodology changes.

## Before You Open a PR

```bash
npm run validate     # structure + version consistency, offline
npm run unit-tests   # grader tests
```

Changes to `skills/**` also need eval evidence — a content-eval run showing the change is net
positive, not just plausible. Single-run case-level deltas are noisy (±25pp observed); see
`benchmarks/README.md` for the multi-run averaging rule. **Never relax a grader rule to make a
case pass.**
