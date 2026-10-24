#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
if [[ "${1:-}" == --install-deps ]]; then
  guest_root /usr/bin/env DEBIAN_FRONTEND=noninteractive /bin/bash -lc \
    'apt-get update && apt-get install -y --no-install-recommends g++ pkg-config qtbase5-dev'
fi
guest /bin/bash "$LOMIRI_GUEST_ROOT/scripts/guest-build-input-compat.sh"
