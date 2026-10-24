#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
[[ $(id -u) == 0 ]] || { echo 'Run this script through scripts/install.sh.' >&2; exit 1; }
apt-get update
candidate=$(apt-cache policy lomiri | awk '/Candidate:/ {print $2}')
[[ -n "$candidate" && "$candidate" != '(none)' ]] || { echo 'No Lomiri package in this distribution. No repository changes performed.' >&2; exit 2; }
# Suppress service startup only during package installation in the PRoot guest.
policy=/usr/sbin/policy-rc.d
backup=$(mktemp -d)
had_policy=0
if [[ -e "$policy" || -L "$policy" ]]; then cp -a "$policy" "$backup/original"; had_policy=1; fi
restore_policy() {
  rm -f -- "$policy"
  if [[ "$had_policy" == 1 ]]; then cp -a "$backup/original" "$policy"; fi
  rm -f -- "$backup/original"
  rmdir "$backup"
}
trap restore_policy EXIT
printf '#!/bin/sh\nexit 101\n' > "$policy"
chmod 755 "$policy"
apt-get install -y --no-install-recommends lomiri mir-platform-graphics-x mir-demos dbus-x11 mesa-utils qtwayland5 xwayland
dpkg-query -W -f='${Package}\t${Version}\n' lomiri qtmir mir-platform-graphics-x mir-demos
