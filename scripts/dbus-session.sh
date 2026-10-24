#!/usr/bin/env bash
set -euo pipefail
project=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
python3 - "$project/runtime/guest-session-env.json" <<'PY'
import json, os, sys
from pathlib import Path
keys = ['DBUS_SESSION_BUS_ADDRESS', 'XDG_RUNTIME_DIR', 'XDG_CONFIG_HOME', 'XDG_CACHE_HOME', 'XDG_DATA_HOME', 'DISPLAY']
p = Path(sys.argv[1])
p.write_text(json.dumps({k: os.environ[k] for k in keys if k in os.environ}))
p.chmod(0o600)
PY
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
if [[ "${LOMIRI_DIRECT:-0}" != 1 ]]; then args+=(--windowgeometry=480x800); fi
if [[ "${LOMIRI_INPUT_TRACE:-0}" == 1 && -f "$project/runtime/lomiri-qml/ShellApplication.qml" ]]; then
  args+=("--qmlfile=$project/runtime/lomiri-qml/ShellApplication.qml")
fi
exec lomiri "${args[@]}"
