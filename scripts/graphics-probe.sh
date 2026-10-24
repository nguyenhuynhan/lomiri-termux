#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
export DISPLAY="$LOMIRI_DISPLAY"
DISPLAY="$LOMIRI_DISPLAY" xrandr --current >/dev/null 2>&1 || { echo 'Open Linux Desktop / run desk before probing.' >&2; exit 2; }
guest /usr/bin/env DISPLAY="$LOMIRI_DISPLAY" LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe \
  /bin/bash -lc '
    echo "GLX probe"
    timeout 20s glxinfo -B || true
    echo "EGL probe"
    timeout 20s eglinfo -B || true
    echo "Mir programs"
    command -v mir_demo_server || true
    command -v miral-shell || true
    echo "Installed versions"
    dpkg-query -W -f="\${Package}\t\${Version}\n" lomiri qtmir mir-platform-graphics-x mir-demos
    echo "Mir platform options"
    timeout 10s miral-shell --help || true
    echo "Qt platform plugins"
    find /usr/lib/aarch64-linux-gnu/qt5/plugins/platforms -maxdepth 1 -name "*.so" -printf "%f\n"
  ' 2>&1 | tee "$PROJECT_ROOT/runtime/graphics-probe.log"
