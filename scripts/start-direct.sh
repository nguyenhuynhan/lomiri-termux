#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
open_window() {
  am start --user 0 -n com.termux.x11/.MainActivity -d termux-x11-window://lomiri-poc >/dev/null 2>&1 || true
  sleep .5
  python "$PROJECT_ROOT/scripts/refresh-direct.py" || true
}
if python "$PROJECT_ROOT/scripts/session-state.py" status >/dev/null; then
  mode=$(python - "$PROJECT_ROOT/runtime/session.json" <<'PY'
import json,sys
print(json.load(open(sys.argv[1])).get('mode','nested'))
PY
)
  if [[ "$mode" == direct ]]; then
    open_window
    exit 0
  fi
  bash "$PROJECT_ROOT/scripts/stop.sh"
fi
export LOMIRI_DIRECT=1
export LOMIRI_DISPLAY=:2
bash "$PROJECT_ROOT/scripts/start.sh"
open_window
