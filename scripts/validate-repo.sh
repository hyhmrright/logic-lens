#!/usr/bin/env bash
# Sanity-check the Logic-Lens repo structure and metadata before a release.
# Fast and offline; safe to run in CI.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

fail=0
check() { if eval "$2"; then echo "  ok  $1"; else echo "  FAIL  $1"; fail=1; fi; }

echo "[1/4] Required skill directories and frontmatter"
for skill in review explain diff locate health fix-all; do
  check "skills/logic-${skill}/SKILL.md exists with name: field" \
    '[[ -f "skills/logic-'"$skill"'/SKILL.md" ]] && grep -q "^name:" "skills/logic-'"$skill"'/SKILL.md"'
done

echo "[2/4] Shared framework files"
for f in common.md logic-risks.md semiformal-guide.md semiformal-checklist.md report-template.md; do
  check "skills/_shared/$f exists" '[[ -f "skills/_shared/'"$f"'" ]]'
done

echo "[3/4] Guide files"
for skill in review explain diff locate health fix-all; do
  check "skills/logic-${skill}/logic-${skill}-guide.md exists" \
    '[[ -f "skills/logic-'"$skill"'/logic-'"$skill"'-guide.md" ]]'
done
check "skills/logic-fix-all phase files present" \
  '[[ -f "skills/logic-fix-all/guide-phases-0-2-consent-scope-health.md" && -f "skills/logic-fix-all/guide-phases-3-5-review-locate-clarify.md" && -f "skills/logic-fix-all/guide-phases-6-9-fix-iterate-report.md" ]]'

echo "[4/5] Benchmark layout"
check "evals/content/v2/evals-v2.json exists" '[[ -f "evals/content/v2/evals-v2.json" ]]'
for skill in review explain diff locate health fix-all; do
  check "evals/trigger/v2/trigger-evals-${skill}.json exists" \
    '[[ -f "evals/trigger/v2/trigger-evals-'"$skill"'.json" ]]'
done
check "benchmarks/index.json exists" '[[ -f "benchmarks/index.json" ]]'
for f in benchmarks/runs/v0.6.4-haiku-baseline.json benchmarks/runs/v0.6.4-haiku-after-skillmd-rewrite.json benchmarks/runs/v0.6.4-sonnet-eval-9-in-session.json; do
  check "$f exists" "[[ -f '$f' ]]"
done

echo "[5/5] Version consistency"
pkg_ver=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' package.json | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
check "package.json version non-empty" "[[ -n '$pkg_ver' ]]"
for mf in .claude-plugin/plugin.json .claude-plugin/marketplace.json .codex-plugin/plugin.json gemini-extension.json; do
  mf_ver=$(grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$mf" | head -1 | sed 's/.*"\([^"]*\)"$/\1/')
  check "$mf matches package.json ($pkg_ver)" "[[ '$mf_ver' == '$pkg_ver' ]]"
done
readme_ver=$(grep -o 'version-[^-]*-blue' README.md | head -1 | sed 's/version-\(.*\)-blue/\1/')
check "README badge matches package.json" "[[ '$readme_ver' == '$pkg_ver' ]]"

echo
if [[ $fail -eq 0 ]]; then
  echo "All checks passed. Repo looks release-ready."
else
  echo "SOME CHECKS FAILED. Fix before tagging a release."
  exit 1
fi
