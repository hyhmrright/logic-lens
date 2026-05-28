---
name: new-skill
description: Scaffold a new logic-* skill in the Logic-Lens repo and wire it into every place a skill must be registered, so no step is missed. Use when adding a seventh (or later) skill to Logic-Lens.
disable-model-invocation: true
---

# new-skill

CLAUDE.md → "Adding a New Skill" is the authoritative checklist. This skill exists to make sure *every* step actually runs — the session-start loop and the eval cases are the ones most often forgotten.

**Read CLAUDE.md's "Adding a New Skill" section now**, then execute its steps for `logic-<NAME>` (ask the user for `<NAME>` if not in `$ARGUMENTS`):

1. **`skills/logic-<NAME>/SKILL.md`** — copy the frontmatter shape from `skills/logic-review/SKILL.md` (`name` + `description`). The `description` MUST include a "Do NOT trigger for:" clause and a "SCOPE … RULE" line distinguishing it from the other skills. Process section = 5–7 numbered items, each citing a guide step. Follow lazy-loading per `skills/_shared/common.md` §13.
2. **`skills/logic-<NAME>/logic-<NAME>-guide.md`** — numbered steps (Step 1, 2, …), each explaining the *why*, concrete examples over abstractions.
3. **`commands/logic-<NAME>.md`** — mirror `commands/logic-review.md`:
   ```markdown
   ---
   description: <one line>
   allowed-tools: Skill
   ---
   Use the Skill tool to invoke `logic-lens:logic-<NAME>`, then follow its instructions exactly. $ARGUMENTS
   ```
4. **`hooks/session-start`** (CLAUDE.md step 6 — easy to miss) — add `logic-<NAME>` to BOTH the `for skill in …` loop and the printed skill list:
   ```bash
   grep -n "for skill in" hooks/session-start
   ```
5. **Eval cases** (CLAUDE.md step 7 — easy to miss) — add 3–5 content cases to `evals/content/v2/evals-v2.json`. Trigger cases under `evals/trigger/v2/` are optional and only catch description regressions (positive cases always score 0% — see CLAUDE.md → Gotchas).
6. **`gemini-extension.json`** — CLAUDE.md says Gemini auto-discovers from `skills/`, but the file *also* enumerates each skill+command under `contribution`. If you want that list complete, add `logic-<NAME>` entries to both `contribution.skills` and `contribution.commands`. (Not checked by `validate-repo.sh`.)
7. **Validate** — run `npm run validate` and confirm all checks pass.
