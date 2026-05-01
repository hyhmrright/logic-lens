#!/usr/bin/env bash
# Shared defaults for Logic-Lens eval scripts.
# Usage: source "$(dirname "${BASH_SOURCE[0]}")/_defaults.sh"
#
# Default to sonnet for cost control. Sonnet 4.6 handles both bulk eval
# queries and extended-thinking proposal steps well at ~5x lower cost than
# Opus. Override with MODEL=claude-opus-4-7 only if you have evidence
# sonnet is producing weak proposals.
MODEL="${MODEL:-claude-sonnet-4-6}"
