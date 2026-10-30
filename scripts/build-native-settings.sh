#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
guest_root /bin/bash -c 'export DEBIAN_FRONTEND=noninteractive; apt-get install -y --no-install-recommends cmake g++ make qtdeclarative5-dev libglib2.0-dev' > "$PROJECT_ROOT/runtime/native-build-deps.log" 2>&1
guest /usr/bin/python3 "$LOMIRI_GUEST_ROOT/scripts/build-native-settings.py" > "$PROJECT_ROOT/runtime/native-build.log" 2>&1
echo 'Native frontend built privately. Restart Lomiri to use it.'
