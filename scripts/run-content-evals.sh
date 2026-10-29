#!/usr/bin/env bash
# Compatibility wrapper for the provider-neutral runner. Codex is the default.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${TAG:-$(git -C "$REPO_ROOT" rev-parse --short HEAD)}"
args=(content --out "$REPO_ROOT/skills-workspace/iteration-$TAG" --jobs "${PARALLEL:-2}")
[[ "${SMOKE:-0}" == "1" ]] && args+=(--smoke)
[[ "${SKIP_GRADE:-0}" == "1" ]] && args+=(--skip-grade)
if [[ -n "${CASES:-}" ]]; then
  read -ra case_ids <<< "$CASES"
  args+=(--cases "${case_ids[@]}")
fi
exec python3 "$REPO_ROOT/scripts/run_evals.py" "${args[@]}" "$@"
