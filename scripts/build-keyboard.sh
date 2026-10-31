#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
guest /bin/bash -c '
set -euo pipefail
mkdir -p runtime/keyboard-addons
g++ -std=c++17 -Wall -Wextra -shared -fPIC -O2 \
  -o runtime/keyboard-addons/liblomirikeyboardfocus.so.new src/keyboard-focus.cpp \
  $(pkg-config --cflags --libs Fcitx5Core)
mv runtime/keyboard-addons/liblomirikeyboardfocus.so.new runtime/keyboard-addons/liblomirikeyboardfocus.so
'
guest /usr/bin/python3 - <<'PY'
import hashlib, json, subprocess
from pathlib import Path
root = Path.cwd()
binary = root / 'runtime/keyboard-addons/liblomirikeyboardfocus.so'
version = subprocess.check_output(['dpkg-query', '-W', '-f=${Version}', 'libfcitx5core7'], text=True)
(root / 'runtime/keyboard-build.json').write_text(json.dumps({
    'core_version': version, 'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
    'source_sha256': hashlib.sha256((root / 'src/keyboard-focus.cpp').read_bytes()).hexdigest()}))
PY
