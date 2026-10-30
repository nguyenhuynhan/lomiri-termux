#!/usr/bin/env bash
set -euo pipefail
project=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
python3 - "$project/runtime/guest-session-env.json" <<'PY'
import json, os, sys
from pathlib import Path
keys = ['DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'DISPLAY', 'PULSE_SERVER', 'PULSE_COOKIE']
p = Path(sys.argv[1])
p.write_text(json.dumps({k: os.environ[k] for k in keys if k in os.environ}))
p.chmod(0o600)
PY
export LOMIRI_CODE_NO_SANDBOX="${LOMIRI_CODE_NO_SANDBOX:-0}"
rm -f "$project/runtime/app-services.ready"
python3 "$project/scripts/guest-app-services.py" > "$project/runtime/app-services.log" 2>&1 &
services_pid=$!
trap 'kill -TERM "$services_pid" 2>/dev/null || true' EXIT
for ((n=0;n<40;n++)); do
  [[ -f "$project/runtime/app-services.ready" ]] && break
  kill -0 "$services_pid" || { cat "$project/runtime/app-services.log"; exit 2; }
  sleep 0.1
done
[[ -f "$project/runtime/app-services.ready" ]] || { echo 'App services did not become ready'; exit 2; }
if [[ "${LOMIRI_TRACE:-0}" == 1 ]]; then
  export LD_PRELOAD="$project/runtime/libcrash-trace.so"
fi
if [[ "${LOMIRI_MOUSE_COMPAT:-0}" == 1 ]]; then
  python3 "$project/scripts/check-input-compat.py" "$project"
  export LD_PRELOAD="$project/runtime/libqt-mouse-dispatch-compat.so${LD_PRELOAD:+:$LD_PRELOAD}"
fi
if [[ "${LOMIRI_INPUT_TRACE:-0}" == 1 && -f "$project/runtime/libqt-input-probe.so" ]]; then
  export LD_PRELOAD="$project/runtime/libqt-input-probe.so${LD_PRELOAD:+:$LD_PRELOAD}"
fi
args=(--mode=shell)
if [[ "${LOMIRI_DIRECT:-0}" == 1 ]]; then
  python3 "$project/scripts/prepare-host-shell.py"
  gsettings set org.gnome.desktop.interface icon-theme suru
  if [[ ! -f "$project/runtime/core-launcher-v1" ]]; then
    gsettings set com.lomiri.Shell.Launcher items "['application:///lomiri-terminal-app.desktop', 'application:///lomiri-filemanager-app.desktop', 'application:///lomiri-chatgpt.desktop', 'application:///lomiri-code.desktop', 'application:///lomiri-calculator-app.desktop']"
    touch "$project/runtime/core-launcher-v1"
  fi
  args+=("--qmlfile=$project/runtime/host-qml/ShellApplication.qml")
fi
if [[ "${LOMIRI_DIRECT:-0}" != 1 ]]; then args+=(--windowgeometry=480x800); fi
if [[ "${LOMIRI_DIRECT:-0}" != 1 && "${LOMIRI_INPUT_TRACE:-0}" == 1 && -f "$project/runtime/lomiri-qml/ShellApplication.qml" ]]; then
  args+=("--qmlfile=$project/runtime/lomiri-qml/ShellApplication.qml")
fi
lomiri "${args[@]}" &
shell_pid=$!
trap 'kill -TERM "$shell_pid" "$services_pid" 2>/dev/null || true' EXIT
trap 'exit 143' TERM
trap 'exit 130' INT
wait "$shell_pid"
