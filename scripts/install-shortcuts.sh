#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
mkdir -p "$HOME/bin" "$HOME/Desktop" "$HOME/.local/share/applications" \
  "$HOME/.shortcuts/tasks" "$HOME/.termux/widget/dynamic_shortcuts"
for action in start stop status; do
  script="$action"
  [[ "$action" != start ]] || script=start-direct
  file="$HOME/bin/lomiri-$action"
  if [[ -e "$file" ]] && ! grep -q 'lomiri-termux project shortcut' "$file"; then
    echo "Existing unrelated command: $file; skipped." >&2
    continue
  fi
  printf '#!%s/bin/bash\n# lomiri-termux project shortcut\nexec "%s/bin/bash" "%s/scripts/%s.sh" "$@"\n' \
    "$PREFIX" "$PREFIX" "$PROJECT_ROOT" "$script" > "$file"
  chmod 700 "$file"
done
for app in code chatgpt; do
  file="$HOME/bin/lomiri-$app"
  if [[ -e "$file" ]] && ! grep -q 'lomiri-termux project shortcut' "$file"; then
    echo "Existing unrelated command: $file; skipped." >&2
    continue
  fi
  printf '#!%s/bin/bash\n# lomiri-termux project shortcut\nexec "%s/bin/bash" "%s/scripts/start-work-app.sh" %s "$@"\n' \
    "$PREFIX" "$PREFIX" "$PROJECT_ROOT" "$app" > "$file"
  chmod 700 "$file"
done
python - "$PROJECT_ROOT" "$PREFIX" <<'PY'
from pathlib import Path
import sys
root, prefix = sys.argv[1:]
for action, title in [('start', 'Lomiri PoC'), ('stop', 'Stop Lomiri PoC')]:
    script = 'start-direct' if action == 'start' else action
    text = ('[Desktop Entry]\nVersion=1.0\nType=Application\n'
            f'Name={title}\nIcon=applications-development\n'
            f'Exec=xfce4-terminal --command="{prefix}/bin/bash {root}/scripts/{script}.sh"\n'
            'Terminal=false\nCategories=Development;\n')
    for folder in [Path.home()/'Desktop', Path.home()/'.local/share/applications']:
        file = folder / f'lomiri-termux-{action}.desktop'
        if file.exists() and 'lomiri-termux' not in file.read_text():
            raise RuntimeError(f'Refusing to overwrite unrelated launcher: {file}')
        file.write_text(text)
        file.chmod(0o700)
    name = 'Lomiri' if action == 'start' else 'Stop Lomiri'
    shortcut = (f'#!{prefix}/bin/bash\n# lomiri-termux project shortcut\n'
                f'exec "{prefix}/bin/bash" "{root}/scripts/{script}.sh"\n')
    for folder in [Path.home()/'.shortcuts/tasks', Path.home()/'.termux/widget/dynamic_shortcuts']:
        file = folder / name
        if file.exists() and 'lomiri-termux project shortcut' not in file.read_text():
            raise RuntimeError(f'Refusing to overwrite unrelated shortcut: {file}')
        file.write_text(shortcut)
        file.chmod(0o700)
for app, name in [('code', 'VSCode (Lomiri)'), ('chatgpt', 'ChatGPT (Lomiri)')]:
    shortcut = (f'#!{prefix}/bin/bash\n# lomiri-termux project shortcut\n'
                f'exec "{prefix}/bin/bash" "{root}/scripts/start-work-app.sh" {app}\n')
    for folder in [Path.home()/'.shortcuts/tasks', Path.home()/'.termux/widget/dynamic_shortcuts']:
        file = folder / name
        if file.exists() and 'lomiri-termux project shortcut' not in file.read_text():
            raise RuntimeError(f'Refusing to overwrite unrelated shortcut: {file}')
        file.write_text(shortcut)
        file.chmod(0o700)
PY
echo 'Commands: lomiri-start, lomiri-stop, lomiri-status, lomiri-code, lomiri-chatgpt. Widget shortcuts installed.'
