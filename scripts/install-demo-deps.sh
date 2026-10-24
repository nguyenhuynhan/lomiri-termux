#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
guest_root /usr/bin/env DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends qmlscene
