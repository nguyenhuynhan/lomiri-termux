#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
{
  date -u +'%Y-%m-%dT%H:%M:%SZ'
  uname -m
  df -h "$PROJECT_ROOT"
  DISPLAY="$LOMIRI_DISPLAY" xrandr --current || true
  guest /bin/bash -lc 'cat /etc/os-release; apt-cache policy lomiri qtmir mir-platform-graphics-x mir-demos; ls -l /tmp/.X11-unix/ 2>/dev/null || true'
} 2>&1 | tee "$PROJECT_ROOT/runtime/preflight.log"
