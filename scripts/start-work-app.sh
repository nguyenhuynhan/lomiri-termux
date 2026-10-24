#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
[[ "${1:-}" == code || "${1:-}" == chatgpt ]] || { echo 'Choose code or chatgpt.' >&2; exit 2; }
bash "$PROJECT_ROOT/scripts/start-direct.sh"
for ((n=0;n<40;n++)); do
  if [[ -S "$PROJECT_ROOT/runtime/work-apps.sock" && -S "$PROJECT_ROOT/runtime/xdg/wayland-0" ]]; then break; fi
  sleep .25
done
exec bash "$PROJECT_ROOT/scripts/work-app.sh" "$@"
