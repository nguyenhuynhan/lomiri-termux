#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")/.."
command -v g++ >/dev/null && pkg-config --exists Qt5Gui || {
  echo 'Build dependencies missing. In Termux: bash scripts/build-input-compat.sh --install-deps' >&2
  exit 2
}
mkdir -p runtime
g++ -Wall -Wextra -shared -fPIC -O2 -Wl,--version-script=src/qt-mouse-dispatch.map \
  -o runtime/libqt-mouse-dispatch-compat.so.new src/qt-mouse-dispatch-compat.cpp \
  $(pkg-config --cflags --libs Qt5Gui) -ldl
g++ -Wall -Wextra -fPIC -O2 -o runtime/input-compat-test tests/input-compat.cpp $(pkg-config --cflags --libs Qt5Gui)
QT_QPA_PLATFORM=offscreen LD_PRELOAD="$PWD/runtime/libqt-mouse-dispatch-compat.so.new" runtime/input-compat-test
mv runtime/libqt-mouse-dispatch-compat.so.new runtime/libqt-mouse-dispatch-compat.so
python3 - <<'PY'
import hashlib, json, subprocess
from pathlib import Path
packages = ['libqt5core5t64', 'libqt5gui5t64', 'qtmir']
library = Path('runtime/libqt-mouse-dispatch-compat.so')
record = {'packages': packages,
          'versions': subprocess.check_output(['dpkg-query', '-W', '-f=${Package}\t${Version}\n', *packages], text=True),
          'sha256': hashlib.sha256(library.read_bytes()).hexdigest()}
Path('runtime/input-compat.json').write_text(json.dumps(record, indent=2) + '\n')
PY
echo 'Input bridge built and tested. Restart Lomiri to load it.'
