---
name: bump-version
description: Bump the Logic-Lens version across all six metadata locations at once (package.json, the four plugin manifests, and the README badge), then validate. Use when cutting a release or when `npm run validate` reports a version mismatch.
disable-model-invocation: true
---

# bump-version

Logic-Lens keeps the version in six places (see CLAUDE.md → Version Sync). Hand-editing them drifts; `validate-repo.sh` only *detects* drift. This skill rewrites all six atomically via `scripts/bump-version.py`.

## Steps

1. **Pick the target version.** If the user passed one in `$ARGUMENTS`, use it. Otherwise read `package.json`'s current `version` and ask whether to bump patch / minor / major.
2. **Run the bump** from the repo root:
   ```bash
   npm run bump-version -- <new-version>     # e.g. npm run bump-version -- 0.7.0
   ```
   It rewrites the `version` field in `package.json`, `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`, `.codex-plugin/plugin.json`, `gemini-extension.json`, and the `README.md` badge — preserving formatting — then runs `validate-repo.sh`.
3. **Confirm** the run ends with "All checks passed." If any file is reported as a mismatch, stop and report which one — do not hand-edit around the script.
4. **CHANGELOG.md is not touched.** For a real release, add a `CHANGELOG.md` entry for the new version yourself.
