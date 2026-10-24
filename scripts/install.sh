#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
guest_root /bin/bash "$LOMIRI_GUEST_ROOT/scripts/guest-install.sh" 2>&1 | tee "$PROJECT_ROOT/runtime/install.log"
