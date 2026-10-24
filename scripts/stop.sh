#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python "$PROJECT_ROOT/scripts/session-state.py" stop
