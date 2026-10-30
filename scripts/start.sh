#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
exec 9>"$PROJECT_ROOT/runtime/start.lock"
flock -x 9
if python "$PROJECT_ROOT/scripts/session-state.py" status >/dev/null; then
  python "$PROJECT_ROOT/scripts/session-state.py" status
  exit 0
fi
if [[ "${LOMIRI_DIRECT:-0}" != 1 ]]; then
  DISPLAY="$LOMIRI_DISPLAY" xrandr --current >/dev/null 2>&1 || { echo 'Open Linux Desktop / run desk first.' >&2; exit 2; }
fi
# Do not pass the startup lock to the long-lived session.
nohup setsid bash "$PROJECT_ROOT/scripts/session.sh" 9>&- > "$PROJECT_ROOT/runtime/session.log" 2>&1 </dev/null &
sleep 3
python "$PROJECT_ROOT/scripts/session-state.py" status || { tail -n 40 "$PROJECT_ROOT/runtime/session.log"; exit 1; }
if [[ "${LOMIRI_DIRECT:-0}" == 1 ]]; then
  for ((n=0;n<120;n++)); do
    if grep -q 'qml: LOMIRI_SHELL_READY' "$PROJECT_ROOT/runtime/session.log"; then break; fi
    python "$PROJECT_ROOT/scripts/session-state.py" status >/dev/null || { tail -n 40 "$PROJECT_ROOT/runtime/session.log"; exit 1; }
    sleep .25
  done
  grep -q 'qml: LOMIRI_SHELL_READY' "$PROJECT_ROOT/runtime/session.log" || {
    echo 'Lomiri shell did not become ready; inspect runtime/session.log.' >&2; exit 1;
  }
fi
echo 'Process started; confirm a visible Lomiri launcher/panel before treating it as working.'
