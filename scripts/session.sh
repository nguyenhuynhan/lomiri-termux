#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
python "$PROJECT_ROOT/scripts/session-state.py" register
child_pid=''
server_pid=''
launcher_pid=''
sync_pid=''
audio_module=''
audio_port=''
cleanup() {
  if [[ -n "$child_pid" ]]; then kill -TERM "$child_pid" 2>/dev/null || true; fi
  if [[ -n "$server_pid" ]]; then kill -TERM "$server_pid" 2>/dev/null || true; fi
  if [[ -n "$launcher_pid" ]]; then kill -TERM "$launcher_pid" 2>/dev/null || true; fi
  if [[ -n "$sync_pid" ]]; then kill -TERM "$sync_pid" 2>/dev/null || true; fi
  if [[ -n "$audio_module" ]]; then
    module_line=$(pactl list short modules 2>/dev/null | awk -v id="$audio_module" '$1 == id') || true
    if [[ "$module_line" == *module-native-protocol-tcp* && "$module_line" == *"port=$audio_port "* ]]; then
      pactl unload-module "$audio_module" 2>/dev/null || true
    fi
  fi
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
# PRoot's emulated UID breaks Unix credentials. Use cookie-authenticated loopback
# and unload only this session's module; never stop the shared Termux daemon.
pulseaudio --start --exit-idle-time=-1 2>/dev/null || true
audio_port=$(python -c 'import socket; s=socket.socket(); s.bind(("127.0.0.1",0)); print(s.getsockname()[1]); s.close()')
audio_module=$(pactl load-module module-native-protocol-tcp listen=127.0.0.1 port="$audio_port" \
  auth-anonymous=0 auth-cookie="$HOME/.config/pulse/cookie" 2> "$PROJECT_ROOT/runtime/audio.log") || audio_module=''
export PULSE_SERVER="${audio_module:+tcp:127.0.0.1:$audio_port}"
export PULSE_COOKIE="$HOME/.config/pulse/cookie"

guest /usr/bin/env DISPLAY="$LOMIRI_DISPLAY" LOMIRI_SOFTWARE_RENDERING="$LOMIRI_SOFTWARE_RENDERING" \
  PULSE_SERVER="$PULSE_SERVER" PULSE_COOKIE="$PULSE_COOKIE" \
  LOMIRI_TRACE="${LOMIRI_TRACE:-0}" \
  LOMIRI_INPUT_TRACE="${LOMIRI_INPUT_TRACE:-0}" \
  LOMIRI_MOUSE_COMPAT="${LOMIRI_MOUSE_COMPAT:-0}" \
  LOMIRI_CODE_NO_SANDBOX="$LOMIRI_CODE_NO_SANDBOX" \
  LOMIRI_DIRECT="${LOMIRI_DIRECT:-0}" LOMIRI_X11_OUTPUT="${LOMIRI_X11_OUTPUT:-480x800}" \
  /bin/bash "$LOMIRI_GUEST_ROOT/scripts/guest-session.sh" &
child_pid=$!
guest /usr/bin/env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  LOMIRI_CODE_NO_SANDBOX="$LOMIRI_CODE_NO_SANDBOX" \
  python3 "$LOMIRI_GUEST_ROOT/scripts/guest-work-apps.py" > "$PROJECT_ROOT/runtime/work-apps-launcher.log" 2>&1 &
launcher_pid=$!
wait "$child_pid"
