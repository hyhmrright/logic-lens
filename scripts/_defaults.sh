#!/usr/bin/env bash
# Shared defaults for Logic-Lens eval scripts.
# Usage: source "$(dirname "${BASH_SOURCE[0]}")/_defaults.sh"
#
# Default to Haiku for eval/benchmark runs — lowest cost for bulk grading.
# Haiku 4.5 is sufficient for trigger-eval classification and content-eval
# scoring; it cuts a full 28-case content run from ~$1-2 to ~$0.10-0.20.
# Override with MODEL=claude-sonnet-4-6 when you need higher accuracy on
# edge cases, or MODEL=claude-opus-4-7 for extended-thinking proposals.
MODEL="${MODEL:-claude-haiku-4-5}"
