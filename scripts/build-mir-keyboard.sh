#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "$0")/common.sh"
# The Debian source must already be extracted with its packaging patches.
# See docs/keyboard-20261031.md for the isolated source/dependency commands.
guest /bin/bash -c '
set -euo pipefail
test "$(dpkg-query -W -f="\${Version}" libmirserver63)" = 2.20.2-2
source_dir=runtime/mir-keyboard/mir-2.20.2
test -f "$source_dir/debian/patches/series"
if ! grep -q "auto const serial = client->next_serial(event);" "$source_dir/src/server/frontend_wayland/input_method_grab_keyboard_v2.cpp"; then
  patch --batch --fuzz=0 -d "$source_dir" -p1 < src/mir-keyboard-grab.patch
fi
if ! grep -q "virtual_keyboard_owned_by" "$source_dir/src/server/frontend_wayland/input_method_grab_keyboard_v2.cpp"; then
  patch --batch --fuzz=0 -d "$source_dir" -p1 < src/mir-keyboard-forward.patch
fi
cmake -S "$source_dir" -B runtime/mir-keyboard/build \
  -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_FLAGS_RELEASE="-O1 -g0 -DNDEBUG" \
  -DCMAKE_C_FLAGS_RELEASE="-O1 -g0 -DNDEBUG" \
  -DCMAKE_SKIP_RPATH=ON \
  -DMIR_ENABLE_TESTS=OFF -DMIR_BUILD_INTERPROCESS_TESTS=OFF \
  -DMIR_FATAL_COMPILE_WARNINGS=OFF -DMIR_USE_PRECOMPILED_HEADERS=OFF \
  -DMIR_PLATFORM=x11 -DMIR_WAYLAND_GENERATOR_EXECUTABLE=/usr/bin/mir_wayland_generator
cmake --build runtime/mir-keyboard/build --target mirserver -j2
mkdir -p runtime/mir-keyboard/lib
cp runtime/mir-keyboard/build/lib/libmirserver.so.63 runtime/mir-keyboard/lib/libmirserver.so.63.new
strip --strip-unneeded runtime/mir-keyboard/lib/libmirserver.so.63.new
'
guest /usr/bin/python3 "$LOMIRI_GUEST_ROOT/scripts/check-mir-keyboard.py" --record
echo 'Private Mir keyboard library built. Save work before restarting Lomiri.'
