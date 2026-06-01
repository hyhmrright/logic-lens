#!/usr/bin/env bash
# Sync the working-copy skills/ into the installed plugin cache so that
# `claude -p` (used by run-content-evals.sh) loads the EDITED skill, not the
# last published one.
#
# Why this exists:
#   content-evals invoke the skill via Claude Code's plugin mechanism, which
#   reads from ~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/skills/.
#   Editing skills/ in the repo does NOT change what the eval sees until you
#   copy it into that cache. Skipping this step silently grades the OLD skill —
#   wasting every token spent on the run.
#
# Usage:
#   bash .claude/skills/sync-skill-cache/scripts/sync-cache.sh          # sync + verify
#   bash .claude/skills/sync-skill-cache/scripts/sync-cache.sh --check  # verify only, no copy
set -euo pipefail

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || (cd "$(dirname "${BASH_SOURCE[0]}")/../../../.." && pwd))"
VERSION="$(python3 -c "import json,sys; print(json.load(open(sys.argv[1]))['version'])" "$REPO_ROOT/package.json")"
CACHE_BASE="$HOME/.claude/plugins/cache/logic-lens-marketplace/logic-lens"
CACHE_DIR="$CACHE_BASE/$VERSION"
SRC="$REPO_ROOT/skills"
DST="$CACHE_DIR/skills"

if [[ ! -d "$CACHE_DIR" ]]; then
  echo "error: plugin cache for version $VERSION not found at:" >&2
  echo "  $CACHE_DIR" >&2
  echo "Available versions:" >&2
  ls -1 "$CACHE_BASE" 2>/dev/null | sed 's/^/  /' >&2 || echo "  (none — is the plugin installed?)" >&2
  echo "If package.json version was just bumped, reinstall/refresh the plugin so the cache dir exists." >&2
  exit 1
fi

CHECK_ONLY=0
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=1

if [[ "$CHECK_ONLY" == "0" ]]; then
  echo "Syncing $SRC/ -> $DST/  (version $VERSION)"
  rsync -a --delete "$SRC/" "$DST/"
fi

# Verify the cache now matches the working copy exactly. A non-empty diff means
# the eval would test stale content — fail loudly so no run is wasted.
if diff -rq "$SRC" "$DST" >/dev/null 2>&1; then
  echo "OK — cache skills/ matches working copy (version $VERSION)"
else
  echo "DRIFT — cache does NOT match working copy:" >&2
  diff -rq "$SRC" "$DST" >&2 || true
  [[ "$CHECK_ONLY" == "1" ]] && echo "Run without --check to sync." >&2
  exit 1
fi
