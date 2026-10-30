#!/usr/bin/env python3
"""Route Android shortcuts through the same app lifecycle as the Lomiri drawer."""
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import dbus

root = Path(__file__).resolve().parent.parent
runtime = root / 'runtime'
state = json.loads((runtime / 'session.json').read_text())
if os.getpgrp() != state['pid']:
    raise RuntimeError('App launcher must belong to the private Lomiri process group.')
endpoint = runtime / 'work-apps.sock'


def launch(app, no_sandbox):
    if no_sandbox and os.environ.get('LOMIRI_CODE_NO_SANDBOX') != '1':
        raise RuntimeError('Set LOMIRI_CODE_NO_SANDBOX=1 in config.env and restart Lomiri to enable this option.')
    env = os.environ.copy()
    env.update(json.loads((runtime / 'guest-session-env.json').read_text()))
    env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    env.pop('LD_PRELOAD', None)
    app_id = 'lomiri-code' if app == 'code' else 'lomiri-chatgpt'
    bus = dbus.bus.BusConnection(env['DBUS_SESSION_BUS_ADDRESS'])
    manager = dbus.Interface(bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'),
                             'org.freedesktop.systemd1.Manager')
    if any(f'--{app_id}--' in str(unit[0]) for unit in manager.ListUnits()):
        return {'ok': True, 'message': f'{app} is already running; select its window in Lomiri.'}
    result = subprocess.run(['/usr/bin/lomiri-app-launch', app_id], env=env,
                            stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=8)
    if result.returncode:
        raise RuntimeError(result.stderr.strip() or f'Application launch failed: {app_id}')
    return {'ok': True, 'message': f'{app} requested through Lomiri; select its window in the launcher.'}


def terminate(_signum, _frame):
    raise SystemExit(0)


signal.signal(signal.SIGTERM, terminate)
signal.signal(signal.SIGINT, terminate)
endpoint.unlink(missing_ok=True)
server = socket.socket(socket.AF_UNIX)
server.bind(str(endpoint))
endpoint.chmod(0o600)
inode = endpoint.stat().st_ino
server.listen(4)
try:
    while True:
        client, _ = server.accept()
        with client:
            client.settimeout(5)
            try:
                request = json.loads(client.recv(4096))
                if not isinstance(request, dict) or set(request) != {'app', 'no_sandbox'} or request['app'] not in ('code', 'chatgpt') or type(request['no_sandbox']) is not bool:
                    raise ValueError('Unsupported application request.')
                result = launch(request['app'], request['no_sandbox'])
            except (OSError, ValueError, RuntimeError, subprocess.TimeoutExpired, dbus.DBusException) as error:
                result = {'ok': False, 'message': str(error)}
            client.sendall(json.dumps(result).encode())
finally:
    server.close()
    if endpoint.exists() and endpoint.stat().st_ino == inode:
        endpoint.unlink()
