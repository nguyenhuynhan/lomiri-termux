#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
[[ "$LOMIRI_DISTRO" == lomiri-debian ]] || { echo 'Work-app installer targets the separate lomiri-debian guest.' >&2; exit 2; }
guest_root /usr/bin/env PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
  /bin/bash "$LOMIRI_GUEST_ROOT/scripts/guest-install-work-apps.sh"
