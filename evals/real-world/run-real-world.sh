#!/usr/bin/env bash
# Real-world probe runner — second validation line beyond content-evals (see README.md).
# For each probe, run logic-review on buggy.* and fixed.* via `claude -p`, then surface
# DETECT (buggy should find a bug) / SILENT (fixed should find none) signals for a human.
# Costs API tokens. NOT auto-scored — real code is too varied for brittle string asserts;
# a green signal is necessary but not sufficient, so read the actual buggy finding.
#
# Usage:
#   bash evals/real-world/run-real-world.sh
#   PROBES_FILTER=001 bash evals/real-world/run-real-world.sh
#   MODEL=claude-opus-4-8 bash evals/real-world/run-real-world.sh
set -euo pipefail

MODEL="${MODEL:-claude-sonnet-4-6}"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROBES_DIR="$ROOT/probes"
OUT="${OUT:-$ROOT/runs/$(date +%Y%m%d-%H%M%S)}"
FILTER="${PROBES_FILTER:-}"

mkdir -p "$OUT"
echo "Model: $MODEL"
echo "Out:   $OUT"
echo

review() {  # $1 = code file, $2 = output file
  local lang="${1##*.}"
  { printf '用 /logic-review 审查下面这段代码的逻辑正确性。\n\n```%s\n' "$lang"
    cat "$1"
    printf '\n```\n'
  } | claude -p --model "$MODEL" > "$2" 2>>"$OUT/stderr.log"
}

# Match a Critical/Warning severity ONLY in finding HEADERS (`### ⚠️ 警告`), never in prose.
# Two false positives this avoids, both hit during bring-up:
#   1. a ✅/no-bug Remedy dry-run line "✅ 偏差消除" — a naive ✅ grep reads it as "no bug"
#   2. a no-bug finding whose Trace *mentions* the word "警告"/"warning" — a whole-file grep
#      reads the mention as a reported Warning
# 💡 Suggestion headers are intentionally NOT blockers: correct code can still have edges.
BLOCKER_HEADER_RE='^#{2,4}[[:space:]].*(🔴|⚠️|🟡|Critical|Warning|严重|警告)'

detect_signal() {  # buggy output should carry a Critical/Warning finding
  grep -qE "$BLOCKER_HEADER_RE" "$1" && echo "DETECT ✓" || echo "miss ✗"
}

silent_signal() {  # fixed output should carry NO Critical/Warning finding (💡 Suggestion ok)
  grep -qE "$BLOCKER_HEADER_RE" "$1" && echo "noisy ✗" || echo "SILENT ✓"
}

shopt -s nullglob
for probe in "$PROBES_DIR"/*/; do
  id="$(basename "$probe")"
  [[ -n "$FILTER" && "$id" != *"$FILTER"* ]] && continue
  buggy=("$probe"buggy.*); fixed=("$probe"fixed.*)
  echo "── $id ──"
  if [[ ${#buggy[@]} -gt 0 ]]; then
    review "${buggy[0]}" "$OUT/$id.buggy.out.md"
    echo "  buggy → $(detect_signal "$OUT/$id.buggy.out.md")"
  fi
  if [[ ${#fixed[@]} -gt 0 ]]; then
    review "${fixed[0]}" "$OUT/$id.fixed.out.md"
    echo "  fixed → $(silent_signal "$OUT/$id.fixed.out.md")"
  fi
  python3 -c "import json,sys;print('  expect:', json.load(open(sys.argv[1]))['expected_bug']['summary'][:96])" "$probe/meta.json" 2>/dev/null || true
  echo
done

echo "Outputs in $OUT"
echo "Read each *.buggy.out.md to confirm the finding names the REAL defect (meta.json → expected_bug)."
