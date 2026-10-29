#!/usr/bin/env bash
# Description-routing evaluation, independent of native plugin activation.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TAG="${TAG:-$(date +%Y%m%d-%H%M%S)}"
args=(routing --out "$REPO_ROOT/skills-workspace/routing-$TAG")
if [[ $# -gt 0 && "$1" != --* ]]; then
  args+=(--skills "$1")
  shift
fi
exec python3 "$REPO_ROOT/scripts/run_evals.py" "${args[@]}" "$@"
