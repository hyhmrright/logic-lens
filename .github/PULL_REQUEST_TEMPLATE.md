## Summary

<!-- What does this PR change and why? One or two sentences. -->

## Scope

<!-- Check all that apply -->
- [ ] SKILL.md (one or more)
- [ ] Guide file (`logic-*-guide.md` or fix-all phase files)
- [ ] Shared framework (`skills/_shared/*`)
- [ ] Evaluation suite (`evals/`)
- [ ] Scripts / tooling
- [ ] Documentation (README, CHANGELOG, release notes)
- [ ] CI / workflows

## Verification

<!-- Required for skill / guide / framework changes -->
- [ ] `bash scripts/validate-repo.sh` passes (22/22 checks)
- [ ] Re-ran relevant evaluation cases (`python3 scripts/grade-iteration.py skills-workspace/<iter>`)
- [ ] Manual smoke-test on at least one representative prompt

## Evaluation impact (if any)

<!-- e.g. "iteration-4 pass_rate 38/38 → 40/40 after this change" -->

## Breaking changes

<!-- None expected, but call out explicitly if any public API (command name,
     trigger word, .logic-lens.yaml field) changes -->
- [ ] This PR introduces no breaking changes
- [ ] This PR has breaking changes (described above)

## Checklist

- [ ] Follows the repository's CLAUDE.md conventions
- [ ] No secrets or PII in added files / commit messages
- [ ] Updated CHANGELOG if user-facing

---
🤖 If this PR was generated with Claude Code, keep the `Generated with Claude Code` footer and `Co-Authored-By` trailer in the commit message.
