#!/usr/bin/env python3
"""Keep a source-built Mir fix confined to the verified Debian ABI."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / 'runtime/mir-keyboard'
LIBRARY = FOLDER / 'lib/libmirserver.so.63'
PACKAGES = ['libmirserver63', 'libmircommon11', 'libmircore2t64', 'libmirplatform30', 'libmirwayland5']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packages():
    return subprocess.check_output(
        ['dpkg-query', '-W', '-f=${Package}\t${Version}\n', *PACKAGES], text=True)


def symbols(path):
    output = subprocess.check_output(['nm', '-D', '--defined-only', str(path)], text=True)
    return {line.split()[-1] for line in output.splitlines() if line.split()}


def main():
    manifest = FOLDER / 'build.json'
    original = Path('/usr/lib/aarch64-linux-gnu/libmirserver.so.63')
    patch = ROOT / 'src/mir-keyboard-grab.patch'
    forward_patch = ROOT / 'src/mir-keyboard-forward.patch'
    if '--record' in sys.argv:
        pending = LIBRARY.with_name(LIBRARY.name + '.new')
        missing = symbols(original) - symbols(pending)
        if missing:
            raise ValueError(f'Private Mir library lacks {len(missing)} installed ABI symbols')
        dependencies = subprocess.check_output(['ldd', str(pending)], text=True)
        if 'not found' in dependencies or '/runtime/mir-keyboard/build/' in dependencies:
            raise ValueError('Private Mir library must resolve the installed dependency libraries')
        subprocess.run([sys.executable, '-c',
                        'import ctypes,sys; ctypes.CDLL(sys.argv[1])', str(pending)], check=True)
        record = {'packages': packages(), 'original_sha256': sha(original),
                  'library_sha256': sha(pending), 'patch_sha256': sha(patch),
                  'forward_patch_sha256': sha(forward_patch)}
        pending.replace(LIBRARY)
        manifest.write_text(json.dumps(record, indent=2) + '\n')
    else:
        record = json.loads(manifest.read_text())
        if (record['packages'] != packages() or record['original_sha256'] != sha(original)
                or record['library_sha256'] != sha(LIBRARY) or record['patch_sha256'] != sha(patch)
                or record['forward_patch_sha256'] != sha(forward_patch)):
            raise ValueError('Mir packages, patch or library changed; rebuild the private keyboard library')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        sys.exit(f'Mir keyboard fix unavailable: {error}')
