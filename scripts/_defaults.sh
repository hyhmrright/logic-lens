#!/usr/bin/env bash
# Compatibility defaults for external wrappers. Active Python runners use the same defaults.
MODEL="${MODEL:-gpt-6.1-sol}"
PROVIDER="${PROVIDER:-codex}"
export MODEL PROVIDER
