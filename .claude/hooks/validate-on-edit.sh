#!/usr/bin/env bash
# PostToolUse hook: re-validate the repo when a skill or metadata file is edited.
# Reads the hook JSON on stdin, runs `npm run validate` only for relevant paths,
# and stays quiet unless validation fails (so successful edits produce no noise).
set -euo pipefail

file_path="$(python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))")"

case "$file_path" in
  *SKILL.md|*plugin.json|*marketplace.json|*gemini-extension.json|*package.json)
    cd "${CLAUDE_PROJECT_DIR:-.}"
    if ! out="$(npm run --silent validate 2>&1)"; then
      printf '%s\n' "$out" >&2
      exit 2
    fi
    ;;
esac
