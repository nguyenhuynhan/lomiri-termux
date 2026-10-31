#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
[[ "$LOMIRI_DISTRO" == lomiri-debian ]] || { echo 'PhotoCraft GPU setup targets lomiri-debian only.' >&2; exit 2; }
guest python3 scripts/prepare-photocraft-gpu.py
shortcut="$HOME/bin/lomiri-photocraft"
mkdir -p "$HOME/bin"
if [[ ! -e "$shortcut" ]] || grep -q 'lomiri-termux project shortcut' "$shortcut"; then
  printf '#!%s/bin/bash\n# lomiri-termux project shortcut\nexec "%s/bin/bash" "%s/scripts/photocraft.sh" "$@"\n' \
    "$PREFIX" "$PREFIX" "$PROJECT_ROOT" > "$shortcut"
  chmod 700 "$shortcut"
else
  echo "Unrelated existing command retained: $shortcut" >&2
fi
