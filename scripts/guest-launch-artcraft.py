#!/usr/bin/env python3
"""Open ArtCraft through the same UAL lifecycle as the application drawer."""
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parent.parent
env = os.environ.copy()
env.update(json.loads((root / 'runtime/guest-session-env.json').read_text()))
env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
for key in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'DISPLAY', 'MIR_SOCKET'):
    env.pop(key, None)
binary = '/usr/bin/lomiri-app-launch'
os.execve(binary, [binary, 'ai.storyteller.artcraft-launcher'], env)
