#!/usr/bin/env python3
"""Refuse a private Qt ABI bridge after package changes or library replacement."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys

root = Path(sys.argv[1])
try:
    record = json.loads((root / 'runtime/input-compat.json').read_text())
    library = root / 'runtime/libqt-mouse-dispatch-compat.so'
    current = subprocess.check_output(
        ['dpkg-query', '-W', '-f=${Package}\t${Version}\n', *record['packages']], text=True)
    if current != record['versions'] or hashlib.sha256(library.read_bytes()).hexdigest() != record['sha256']:
        raise ValueError('Qt/QtMir packages or bridge changed')
except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
    sys.exit(f'Lomiri input bridge is missing or outdated ({error}). Run bash scripts/build-input-compat.sh in Termux.')
