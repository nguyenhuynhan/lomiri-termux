#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
[[ -S "$PROJECT_ROOT/runtime/xdg/wayland-0" ]] || { echo 'Open Lomiri first.' >&2; exit 2; }
exec proot-distro login "$LOMIRI_DISTRO" --user "$LOMIRI_USER" --shared-tmp \
  --bind "$PROJECT_ROOT:$LOMIRI_GUEST_ROOT" --work-dir "$LOMIRI_GUEST_ROOT" -- \
  /usr/bin/python3 "$LOMIRI_GUEST_ROOT/scripts/guest-launch-photocraft.py"
