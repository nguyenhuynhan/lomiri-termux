#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
if guest /usr/bin/python3 "$LOMIRI_GUEST_ROOT/scripts/check-mir-keyboard.py"; then
  exit 0
fi
guest /bin/bash -c 'test "$(dpkg-query -W -f="\${Version}" libmirserver63)" = 2.20.2-2'
mkdir -p "$PROJECT_ROOT/runtime/mir-keyboard/apt-lists/partial"
cat > "$PROJECT_ROOT/runtime/mir-keyboard/sources.list" <<'EOF'
deb http://deb.debian.org/debian trixie main
deb http://deb.debian.org/debian trixie-updates main
deb http://deb.debian.org/debian-security trixie-security main
deb-src http://deb.debian.org/debian trixie main
EOF
apt_options=(-o "Dir::Etc::sourcelist=$LOMIRI_GUEST_ROOT/runtime/mir-keyboard/sources.list"
  -o Dir::Etc::sourceparts=- -o "Dir::State::lists=$LOMIRI_GUEST_ROOT/runtime/mir-keyboard/apt-lists")
guest_root apt-get "${apt_options[@]}" update
guest_root /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get "${apt_options[@]}" \
  build-dep --no-install-recommends -y mir=2.20.2-2
guest /bin/bash -c '
set -euo pipefail
cd runtime/mir-keyboard
if [[ ! -f mir-2.20.2/debian/patches/series ]]; then
  apt-get -o Dir::Etc::sourcelist="$PWD/sources.list" -o Dir::Etc::sourceparts=- \
    -o Dir::State::lists="$PWD/apt-lists" source mir=2.20.2-2
fi
'
bash "$PROJECT_ROOT/scripts/build-mir-keyboard.sh"
