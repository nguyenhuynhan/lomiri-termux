#!/usr/bin/env bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
[[ $(id -u) == 0 ]] || { echo 'Use scripts/install-work-apps.sh from Termux.' >&2; exit 2; }
cd -- "$(dirname -- "$0")/.."
python3 - <<'PY'
import hashlib, json, shutil, urllib.request
from pathlib import Path
runtime = Path('runtime')
runtime.mkdir(exist_ok=True)
with urllib.request.urlopen('https://update.code.visualstudio.com/api/update/linux-deb-arm64/stable/latest', timeout=60) as response:
    release = json.load(response)
target = runtime / 'code-arm64.deb'
expected = release['sha256hash'].lower()
if not target.exists() or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
    with urllib.request.urlopen(release['url'], timeout=120) as response, target.with_suffix('.partial').open('wb') as output:
        shutil.copyfileobj(response, output)
    if hashlib.sha256(target.with_suffix('.partial').read_bytes()).hexdigest() != expected:
        raise RuntimeError('Official VSCode package checksum mismatch.')
    target.with_suffix('.partial').replace(target)
(runtime / 'vscode-release.json').write_text(json.dumps(release, indent=2))
print('Verified official VSCode ARM64 package:', release['productVersion'])
PY
printf 'code code/add-microsoft-repo boolean false\n' | debconf-set-selections
apt-get update
apt-get install -y --no-install-recommends "$PWD/runtime/code-arm64.deb" firefox-esr
echo 'Packages installed. Restart Lomiri, then test the application launchers.'
