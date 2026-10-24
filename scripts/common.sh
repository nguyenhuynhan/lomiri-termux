#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
declare -A command_overrides=()
for name in LOMIRI_DISTRO LOMIRI_USER LOMIRI_DISPLAY LOMIRI_SOFTWARE_RENDERING LOMIRI_MOUSE_COMPAT LOMIRI_INPUT_TRACE LOMIRI_CODE_NO_SANDBOX; do
  if [[ -v "$name" ]]; then command_overrides[$name]=${!name}; fi
done
if [[ -f "$PROJECT_ROOT/config.env" ]]; then source "$PROJECT_ROOT/config.env"; fi
for name in "${!command_overrides[@]}"; do printf -v "$name" '%s' "${command_overrides[$name]}"; done
LOMIRI_DISTRO=${LOMIRI_DISTRO:-lomiri-debian}
LOMIRI_USER=${LOMIRI_USER:-dev}
LOMIRI_DISPLAY=${LOMIRI_DISPLAY:-:1}
LOMIRI_SOFTWARE_RENDERING=${LOMIRI_SOFTWARE_RENDERING:-1}
LOMIRI_MOUSE_COMPAT=${LOMIRI_MOUSE_COMPAT:-1}
LOMIRI_INPUT_TRACE=${LOMIRI_INPUT_TRACE:-0}
LOMIRI_CODE_NO_SANDBOX=${LOMIRI_CODE_NO_SANDBOX:-0}
LOMIRI_GUEST_ROOT=/home/dev/projects/lomiri-termux
PREFIX=${PREFIX:-/data/data/com.termux/files/usr}
export PATH="${HOME}/bin:$PREFIX/bin:/system/bin:$PATH"
mkdir -p "$PROJECT_ROOT/runtime"
# PRoot inherits the Android fd limit; a modest limit avoids slow apt/GPG probes.
ulimit -n 1024
guest() {
  proot-distro login "$LOMIRI_DISTRO" --user "$LOMIRI_USER" --shared-tmp \
    --bind "$PROJECT_ROOT:$LOMIRI_GUEST_ROOT" --work-dir "$LOMIRI_GUEST_ROOT" -- "$@"
}
guest_root() {
  proot-distro login "$LOMIRI_DISTRO" --shared-tmp \
    --bind "$PROJECT_ROOT:$LOMIRI_GUEST_ROOT" --work-dir "$LOMIRI_GUEST_ROOT" -- "$@"
}
