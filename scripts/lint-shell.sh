#!/usr/bin/env bash
# Lint every tracked shell script with shellcheck.
#
# Probe fixtures under evals/real-world/probes/ are excluded on purpose: they are
# deliberately buggy test data, not code, and linting them would always fail.
#
# Note: shellcheck is whatever the environment provides (GitHub's ubuntu runner
# ships 0.9.0; Homebrew is ahead of that), so the version is printed below to
# make a "green locally, red in CI" divergence self-explaining.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

mapfile -t scripts < <(git ls-files '*.sh' ':!evals/real-world/probes/**')
scripts+=("hooks/session-start")   # a bash script without the .sh extension

# Guard against a silently empty list (not a git checkout, or a broken pathspec):
# the linter would otherwise check almost nothing and still exit 0.
if [[ ${#scripts[@]} -lt 2 ]]; then
  echo "error: found no tracked shell scripts — is this a git checkout?" >&2
  exit 1
fi

shellcheck --version | grep '^version:'
echo "linting ${#scripts[@]} scripts"
shellcheck -x -P SCRIPTDIR "${scripts[@]}"
