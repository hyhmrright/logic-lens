---
name: sync-skill-cache
description: Sync the Logic-Lens working-copy skills/ into the installed plugin cache so content-evals test the EDITED skill, not the last published one. ALWAYS run this after editing any skills/**/SKILL.md or guide/_shared file and BEFORE running content-evals — otherwise the eval silently grades stale content and every token is wasted. Also use to verify the cache is in sync ("is the cache fresh?", "did my edit take effect in evals?", "check skill cache drift").
disable-model-invocation: true
---

# sync-skill-cache

content-evals invoke each skill through Claude Code's plugin mechanism, which loads from
`~/.claude/plugins/cache/logic-lens-marketplace/logic-lens/<version>/skills/` — **not** the
repo's `skills/`. Editing `skills/` changes nothing the eval sees until you copy it into the
cache. This is the single most expensive footgun in the iteration loop: skip it and you grade
the previous skill while believing you tested your change.

## Steps

1. **Sync + verify** from the repo root:
   ```bash
   bash .claude/skills/sync-skill-cache/scripts/sync-cache.sh
   ```
   The script reads the active version from `package.json`, rsyncs `skills/` into the matching
   cache dir (`--delete`, so removed files are removed in the cache too), then diffs the two to
   confirm they are byte-identical. It prints `OK …` on success.

2. **If it prints `DRIFT` or a missing-cache error:** do not run evals. The two common causes:
   - The cache dir for the current `package.json` version doesn't exist (plugin not installed at
     this version) — reinstall/refresh the plugin, or check you didn't just bump the version
     without refreshing the cache.
   - rsync was blocked — rerun and read the diff list it prints.

3. **Verify-only mode** (no copy) to answer "is the cache fresh?":
   ```bash
   bash .claude/skills/sync-skill-cache/scripts/sync-cache.sh --check
   ```

This skill is the mandatory gate between editing a skill and grading it. The `iterate-skill`
orchestrator calls it automatically; run it by hand whenever you edit a skill outside that loop.
