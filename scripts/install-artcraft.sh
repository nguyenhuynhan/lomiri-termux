#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
[[ "$LOMIRI_DISTRO" == lomiri-debian ]] || { echo 'ArtCraft setup targets lomiri-debian only.' >&2; exit 2; }
version=0.11.1
file="artcraft-launcher-$version-linux-aarch64.deb"
downloads="$PROJECT_ROOT/runtime/artcraft-downloads"
mkdir -p "$downloads"
expected=89e3eadc69667dc117b5d7950c14311e28c4732f2691fec3b4ac9453eab6861b
if [[ ! -f "$downloads/$file" ]] || [[ "$(sha256sum "$downloads/$file" | cut -d' ' -f1)" != "$expected" ]]; then
  curl -fLsS --retry 2 --connect-timeout 20 --max-time 900 -C - \
    -o "$downloads/$file" "https://github.com/storytold/craft-launcher/releases/download/v$version/$file"
fi
curl -fLsS --retry 2 --connect-timeout 20 --max-time 120 \
  -o "$downloads/SHA256SUMS-$version.txt" "https://github.com/storytold/craft-launcher/releases/download/v$version/SHA256SUMS.txt"
python - "$downloads" "$file" "$version" <<'PY'
import hashlib, sys
from pathlib import Path
folder, name, version = sys.argv[1:]
folder = Path(folder)
expected = '89e3eadc69667dc117b5d7950c14311e28c4732f2691fec3b4ac9453eab6861b'
lines = (folder / f'SHA256SUMS-{version}.txt').read_text().splitlines()
published = next(line.split()[0] for line in lines if line.split()[-1].lstrip('*') == name)
actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
if actual != expected or actual != published:
    sys.exit('Official SHA-256 mismatch; refusing installation.')
print(f'Verified ArtCraft Launcher {version}: {actual}')
PY
guest_root bash -c '
  set -e
  [[ "$(dpkg --print-architecture)" == arm64 ]]
  dpkg-deb --info "$1"
  apt-get --simulate --no-remove install "$1"
  DEBIAN_FRONTEND=noninteractive apt-get --no-remove -y install "$1"
  /usr/bin/artcraft-launcher --version
' bash "$LOMIRI_GUEST_ROOT/runtime/artcraft-downloads/$file"
guest python3 scripts/prepare-artcraft.py
shortcut="$HOME/bin/lomiri-artcraft"
mkdir -p "$HOME/bin"
if [[ ! -e "$shortcut" ]] || grep -q 'lomiri-termux project shortcut' "$shortcut"; then
  printf '#!%s/bin/bash\n# lomiri-termux project shortcut\nexec "%s/bin/bash" "%s/scripts/artcraft.sh" "$@"\n' \
    "$PREFIX" "$PREFIX" "$PROJECT_ROOT" > "$shortcut"
  chmod 700 "$shortcut"
else
  echo "Unrelated existing command retained: $shortcut" >&2
fi
echo 'ArtCraft is installed. Open ArtCraft Launcher in Lomiri, or run lomiri-artcraft.'
