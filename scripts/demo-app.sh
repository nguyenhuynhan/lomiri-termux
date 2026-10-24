#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python "$PROJECT_ROOT/scripts/session-state.py" status >/dev/null || { echo 'Start the Lomiri session first.' >&2; exit 2; }
guest /usr/bin/env LOMIRI_INPUT_TRACE="${LOMIRI_INPUT_TRACE:-0}" python3 "$LOMIRI_GUEST_ROOT/scripts/guest-demo.py" 2>&1 | tee "$PROJECT_ROOT/runtime/demo.log"
