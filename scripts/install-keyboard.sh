#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
guest_root /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  fcitx5 fcitx5-unikey fcitx5-frontend-qt5 fcitx5-frontend-gtk3 \
  python3-dbus python3-gi g++ pkg-config libfcitx5core-dev
bash "$PROJECT_ROOT/scripts/build-keyboard.sh"
bash "$PROJECT_ROOT/scripts/install-mir-keyboard.sh"
touch "$PROJECT_ROOT/runtime/keyboard-enabled"
echo 'UniKey installed for Lomiri. Save work, then restart Lomiri. Select English on the Android keyboard.'
