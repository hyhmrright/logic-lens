#!/usr/bin/env bash
# Run the content eval cases in evals/content/v2/evals-v2.json against `claude -p`,
# write each output to skills-workspace/iteration-<TAG>/eval-<id>/output.md,
# then call grade-iteration.py to produce a pass-rate summary.
#
# Why a separate runner:
#   grade-iteration.py is the *grader* (rule-based; needs no API).
#   This is the *runner* (calls Claude; needs the `claude` CLI on PATH and an API key).
#   Splitting them lets you grade pre-existing outputs (e.g. from CI artifacts)
#   without re-spending tokens, and lets you swap the model used for runs
#   without touching the grader.
#
# Cost note:
#   Each case is one `claude -p` invocation. The current case count is read from
#   evals/content/v2/evals-v2.json at runtime, with a fallback to the legacy
#   evals/v2/evals-v2.json path. Sonnet 4.6 default cost scales with that count;
#   Opus is ~5x. Haiku is ~10x cheaper but fails format-compliance rules — use
#   only for cost experiments.
#
# Usage:
#   bash scripts/run-content-evals.sh                      # tag = current git short SHA
#   TAG=baseline bash scripts/run-content-evals.sh         # custom tag
#   CASES="200 201 202" bash scripts/run-content-evals.sh  # subset of case ids
#   SMOKE=1 bash scripts/run-content-evals.sh              # one case per mode (~$0.10)
#   PARALLEL=8 bash scripts/run-content-evals.sh           # bump parallelism (default 6)
#   MODEL=claude-opus-4-7 bash scripts/run-content-evals.sh
#   SKIP_GRADE=1 bash scripts/run-content-evals.sh         # run only, don't auto-grade
#
# Output:
#   skills-workspace/iteration-<TAG>/
#     eval-<id>/prompt.md     # exact prompt sent to claude (reproducibility)
#     eval-<id>/output.md     # claude's response — only written on success
#     eval-<id>/stderr.log    # claude's stderr if the call failed
#     eval-<id>/grading.json  # written by grade-iteration.py
#     summary.json            # overall + per-mode pass rates
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EVALS_JSON=""
for candidate in \
  "$REPO_ROOT/evals/content/v2/evals-v2.json" \
  "$REPO_ROOT/evals/v2/evals-v2.json"; do
  if [[ -f "$candidate" ]]; then
    EVALS_JSON="$candidate"
    break
  fi
done
if [[ -z "$EVALS_JSON" ]]; then
  echo "error: eval file not found at evals/content/v2/evals-v2.json or evals/v2/evals-v2.json" >&2
  exit 1
fi
# Content evals require semi-formal format compliance (Premises/Trace/Divergence/
# Fault Confidence labels). Haiku skips structured output and fails ~60% of rules.
# Set sonnet as content-eval default BEFORE sourcing _defaults.sh so that haiku
# (the trigger-eval default) does not override it.
MODEL="${MODEL:-claude-sonnet-4-6}"
# shellcheck source=_defaults.sh
source "$(dirname "${BASH_SOURCE[0]}")/_defaults.sh"
TAG="${TAG:-$(git -C "$REPO_ROOT" rev-parse --short HEAD 2>/dev/null || date +%Y%m%d-%H%M%S)}"
ITER_DIR="$REPO_ROOT/skills-workspace/iteration-$TAG"
SKIP_GRADE="${SKIP_GRADE:-0}"
PARALLEL="${PARALLEL:-6}"

if ! command -v claude >/dev/null 2>&1; then
  echo "error: 'claude' CLI not found on PATH. Install from https://claude.ai/download" >&2
  exit 1
fi
if [[ ! -f "$EVALS_JSON" ]]; then
  echo "error: eval file not found at $EVALS_JSON" >&2
  exit 1
fi
if ! command -v python3 >/dev/null 2>&1; then
  echo "error: 'python3' not found on PATH" >&2
  exit 1
fi

mkdir -p "$ITER_DIR"
echo "Output dir: $ITER_DIR"
echo "Model:      $MODEL"
echo "Parallel:   $PARALLEL"

# Resolve case-id list — SMOKE / CASES env override, else every case in the JSON.
# bash 3.2 (macOS default) lacks `mapfile`, so use the portable read-loop.
CASE_IDS=()
if [[ "${SMOKE:-0}" == "1" ]]; then
  # Cheapest broad sanity check: one case per mode.
  CASE_IDS=(1 5 6 7 8 9)
elif [[ -n "${CASES:-}" ]]; then
  read -ra CASE_IDS <<< "$CASES"
else
  while IFS= read -r line; do
    CASE_IDS+=("$line")
  done < <(python3 -c "
import json
for c in json.load(open('$EVALS_JSON'))['evals']:
    print(c['id'])
")
fi
echo "Cases:      ${#CASE_IDS[@]} total"
echo

# One-shot extraction: write prompt.md + .name for every case in a single Python pass.
# Replaces the previous 24× python startup + 24× JSON parse inside the loop.
python3 - "$EVALS_JSON" "$ITER_DIR" "${CASE_IDS[@]}" <<'PY'
import json, os, sys
evals_path, iter_dir = sys.argv[1], sys.argv[2]
wanted = {int(x) for x in sys.argv[3:]}
cases = {c['id']: c for c in json.load(open(evals_path))['evals']}
missing = wanted - cases.keys()
if missing:
    sys.exit(f"case id(s) not found in evals JSON: {sorted(missing)}")
for cid in wanted:
    c = cases[cid]
    d = os.path.join(iter_dir, f"eval-{cid}")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, 'prompt.md'), 'w') as f:
        f.write(c['prompt'])
    with open(os.path.join(d, '.name'), 'w') as f:
        f.write(c['name'])
PY

# Worker function exported for xargs -P parallelism.
# Writes to a .partial tempfile and atomically renames on success — so a
# crashed/aborted run never leaves a half-written output.md that the next
# idempotent run would mistake for a completed case.
run_case() {
  local cid="$1"
  local case_dir="$ITER_DIR/eval-$cid"
  local prompt_file="$case_dir/prompt.md"
  local output_file="$case_dir/output.md"
  local tmp_out="$case_dir/output.md.partial"
  local name
  if [[ -s "$output_file" ]]; then
    echo "[$cid] skip — output.md already exists"
    return 0
  fi
  name=$(cat "$case_dir/.name")
  echo "[$cid] $name → calling claude -p"
  if claude -p --model "$MODEL" < "$prompt_file" > "$tmp_out" 2> "$case_dir/stderr.log"; then
    mv "$tmp_out" "$output_file"
  else
    local rc=$?
    rm -f "$tmp_out"
    echo "  ! [$cid] claude exited $rc, see $case_dir/stderr.log" >&2
  fi
}
export -f run_case
export ITER_DIR MODEL

# `set -euo pipefail` is per-shell and not inherited by xargs's child bash, so re-arm it
# inside the worker shell; otherwise per-case failures inside run_case would be silent.
printf '%s\n' "${CASE_IDS[@]}" | xargs -P "$PARALLEL" -I{} bash -c 'set -euo pipefail; run_case "$@"' _ {}

echo
if [[ "$SKIP_GRADE" == "1" ]]; then
  echo "SKIP_GRADE=1 — leaving outputs ungraded. Run later with:"
  echo "  python3 scripts/grade-iteration.py $ITER_DIR"
  exit 0
fi

python3 "$REPO_ROOT/scripts/grade-iteration.py" "$ITER_DIR"
