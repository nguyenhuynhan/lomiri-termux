#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
[[ "${1:-}" == code || "${1:-}" == chatgpt ]] || { echo 'Choose code or chatgpt.' >&2; exit 2; }
bash "$PROJECT_ROOT/scripts/start-direct.sh"
for ((n=0;n<120;n++)); do
  if [[ -S "$PROJECT_ROOT/runtime/work-apps.sock" && -S "$PROJECT_ROOT/runtime/xdg/wayland-0" ]] && \
      grep -q 'qml: LOMIRI_SHELL_READY' "$PROJECT_ROOT/runtime/session.log"; then break; fi
  sleep .25
done
grep -q 'qml: LOMIRI_SHELL_READY' "$PROJECT_ROOT/runtime/session.log" || { echo 'Lomiri shell is not ready.' >&2; exit 2; }
exec bash "$PROJECT_ROOT/scripts/work-app.sh" "$@"
