#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
new_distro=lomiri-debian
if ! proot-distro login "$new_distro" -- /bin/true >/dev/null 2>&1; then
  proot-distro install debian:trixie --name "$new_distro"
fi
LOMIRI_DISTRO=$new_distro
guest_root /bin/bash -lc 'id dev >/dev/null 2>&1 || useradd -m -s /bin/bash dev; mkdir -p /home/dev/projects'
guest_root /bin/bash "$LOMIRI_GUEST_ROOT/scripts/guest-install.sh" 2>&1 | tee "$PROJECT_ROOT/runtime/install-debian.log"
python - "$PROJECT_ROOT/config.env" <<'PY'
from pathlib import Path
import sys
p = Path(sys.argv[1])
lines = p.read_text().splitlines() if p.exists() else []
lines = [s for s in lines if not s.startswith('LOMIRI_DISTRO=')]
lines.append('LOMIRI_DISTRO=lomiri-debian')
p.write_text('\n'.join(lines) + '\n')
PY
echo 'PoC now uses lomiri-debian. mobile-ubuntu remains available for existing coding tools.'
