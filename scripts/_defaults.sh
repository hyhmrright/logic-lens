#!/usr/bin/env bash
# Shared defaults for Logic-Lens eval scripts.
# Usage: source "$(dirname "${BASH_SOURCE[0]}")/_defaults.sh"
#
# Two-tier model strategy:
#   trigger-evals  — haiku (simple yes/no classification, ~$0.01/run)
#   content-evals  — sonnet (semi-formal format compliance required; haiku
#                    skips Premises/Trace/Divergence labels, ~60% rule failures)
#
# run-content-evals.sh sets MODEL=claude-sonnet-4-6 BEFORE sourcing this file,
# so the haiku fallback here applies only to trigger-evals and other scripts
# that do not pre-set MODEL.
# Override either script with MODEL=<id> to force a specific model.
MODEL="${MODEL:-claude-haiku-4-5}"
