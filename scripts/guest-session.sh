#!/usr/bin/env bash
set -euo pipefail
project=$(cd -- "$(dirname -- "$0")/.." && pwd -P)
# Private writable runtime/config avoids importing the user's other desktop session.
export XDG_RUNTIME_DIR="$project/runtime/xdg"
export XDG_CONFIG_HOME="$project/runtime/config"
export XDG_CACHE_HOME="$project/runtime/cache"
export XDG_DATA_HOME="$project/runtime/data"
export LOMIRI_APP_LAUNCH_SYSTEMD_CGROUP_ROOT="$project/runtime/app-pids"
mkdir -p "$LOMIRI_APP_LAUNCH_SYSTEMD_CGROUP_ROOT"
mkdir -p "$XDG_RUNTIME_DIR" "$XDG_CONFIG_HOME" "$XDG_CACHE_HOME" "$XDG_DATA_HOME"
chmod 700 "$XDG_RUNTIME_DIR"
export XDG_CURRENT_DESKTOP=Lomiri
export QT_QPA_PLATFORM=mirserver
export GRID_UNIT_PX=8
export QSG_RENDER_LOOP=basic
export MIR_SERVER_CONSOLE_PROVIDER=none
export MIR_SERVER_X11_OUTPUT="${LOMIRI_X11_OUTPUT:-480x800}"
export MIR_SERVER_X11_WINDOW_TITLE='Lomiri Termux PoC'
if [[ "${LOMIRI_INPUT_TRACE:-0}" == 1 ]]; then
  export MIR_SERVER_INPUT_REPORT=log
  export MIR_SERVER_SEAT_REPORT=log
  export QT_LOGGING_RULES='qtmir.mir.input.debug=true;qtmir.applications.debug=true;qtmir.surfaces.debug=true'
fi
if [[ "${LOMIRI_SOFTWARE_RENDERING:-1}" == 1 ]]; then
  export LIBGL_ALWAYS_SOFTWARE=1
  export GALLIUM_DRIVER=llvmpipe
fi
unset DBUS_SESSION_BUS_ADDRESS SESSION_MANAGER WAYLAND_DISPLAY MIR_SOCKET
exec dbus-run-session -- bash "$project/scripts/dbus-session.sh"
