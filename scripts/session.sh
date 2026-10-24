#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python "$PROJECT_ROOT/scripts/session-state.py" register
child_pid=''
server_pid=''
launcher_pid=''
sync_pid=''
cleanup() {
  if [[ -n "$child_pid" ]]; then kill -TERM "$child_pid" 2>/dev/null || true; fi
  if [[ -n "$server_pid" ]]; then kill -TERM "$server_pid" 2>/dev/null || true; fi
  if [[ -n "$launcher_pid" ]]; then kill -TERM "$launcher_pid" 2>/dev/null || true; fi
  if [[ -n "$sync_pid" ]]; then kill -TERM "$sync_pid" 2>/dev/null || true; fi
}
trap cleanup EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
if [[ "${LOMIRI_DIRECT:-0}" == 1 ]]; then
  if DISPLAY="$LOMIRI_DISPLAY" xrandr --current >/dev/null 2>&1; then
    echo "Display $LOMIRI_DISPLAY is already in use; refusing to replace another X server." >&2
    exit 2
  fi
  termux-x11 "$LOMIRI_DISPLAY" -tag lomiri-poc -nolisten tcp > "$PROJECT_ROOT/runtime/direct-x11.log" 2>&1 &
  server_pid=$!
  for ((n=0;n<40;n++)); do
    if DISPLAY="$LOMIRI_DISPLAY" xrandr --current >/dev/null 2>&1; then break; fi
    kill -0 "$server_pid" 2>/dev/null || { cat "$PROJECT_ROOT/runtime/direct-x11.log"; exit 2; }
    sleep 0.25
  done
  am start --user 0 -n com.termux.x11/.MainActivity -d termux-x11-window://lomiri-poc >/dev/null 2>&1 || true
  sleep 2
  LOMIRI_X11_OUTPUT=$(DISPLAY="$LOMIRI_DISPLAY" xrandr --current | sed -n 's/.*current \([0-9]*\) x \([0-9]*\),.*/\1x\2/p' | head -n 1)
  [[ -n "$LOMIRI_X11_OUTPUT" ]] || { echo 'Direct X11 server is not ready.' >&2; exit 2; }
  python "$PROJECT_ROOT/scripts/display-sync.py" "$LOMIRI_DISPLAY" > "$PROJECT_ROOT/runtime/display-sync.log" 2>&1 &
  sync_pid=$!
fi
guest /usr/bin/env DISPLAY="$LOMIRI_DISPLAY" LOMIRI_SOFTWARE_RENDERING="$LOMIRI_SOFTWARE_RENDERING" \
  LOMIRI_TRACE="${LOMIRI_TRACE:-0}" \
  LOMIRI_INPUT_TRACE="${LOMIRI_INPUT_TRACE:-0}" \
  LOMIRI_MOUSE_COMPAT="${LOMIRI_MOUSE_COMPAT:-0}" \
  LOMIRI_DIRECT="${LOMIRI_DIRECT:-0}" LOMIRI_X11_OUTPUT="${LOMIRI_X11_OUTPUT:-480x800}" \
  /bin/bash "$LOMIRI_GUEST_ROOT/scripts/guest-session.sh" &
child_pid=$!
guest /usr/bin/env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  python3 "$LOMIRI_GUEST_ROOT/scripts/guest-work-apps.py" > "$PROJECT_ROOT/runtime/work-apps-launcher.log" 2>&1 &
launcher_pid=$!
wait "$child_pid"
