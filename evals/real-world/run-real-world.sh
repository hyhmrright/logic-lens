#!/usr/bin/env bash
# Compatibility wrapper; no provider-specific runtime required.
set -euo pipefail
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
exec python3 "$REPO_ROOT/scripts/run_probes.py" "$@"
