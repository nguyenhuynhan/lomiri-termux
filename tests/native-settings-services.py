#!/usr/bin/env python3
"""Check native launch, isolation, singleton reuse and owned stop on the phone."""
import json
import os
from pathlib import Path
import subprocess
import time

import dbus

root = Path(__file__).resolve().parent.parent
env = os.environ.copy()
env.update(json.loads((root / 'runtime/guest-session-env.json').read_text()))
env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
bus = dbus.bus.BusConnection(env['DBUS_SESSION_BUS_ADDRESS'])
manager = dbus.Interface(bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1'),
                         'org.freedesktop.systemd1.Manager')
name = 'lomiri-app-launch--application-legacy--lomiri-system-settings--.service'


def units():
    result = {}
    for unit in manager.ListUnits():
        properties = dbus.Interface(bus.get_object('org.freedesktop.systemd1', unit[6]),
                                    'org.freedesktop.DBus.Properties')
        result[str(unit[0])] = int(properties.Get('org.freedesktop.systemd1.Service', 'MainPID'))
    return result


others = {key: pid for key, pid in units().items() if key != name}
desktop = root / 'runtime/data/applications/lomiri-system-settings.desktop'
assert desktop.read_bytes() == Path('/usr/share/applications/lomiri-system-settings.desktop').read_bytes()
print('PASS: packaged native desktop entry restored unchanged')
if name not in units():
    subprocess.run(['/usr/bin/lomiri-app-launch', 'lomiri-system-settings'],
                   env=env, check=True, timeout=15)
    time.sleep(2)
pid = units()[name]
owner = json.loads((root / 'runtime/session.json').read_text())['pid']
assert os.getpgid(pid) == owner
assert Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')[0].endswith(b'lomiri-system-settings')
app_env = dict(entry.split(b'=', 1) for entry in Path(f'/proc/{pid}/environ').read_bytes().split(b'\0') if b'=' in entry)
assert app_env[b'QT_QPA_PLATFORM'] == b'wayland'
assert app_env[b'XDG_CONFIG_HOME'].decode() == str(root / 'runtime/config')
assert app_env[b'XDG_DATA_DIRS'].decode().endswith(str(root / 'runtime/native-data'))
assert b'LD_PRELOAD' not in app_env
record = root / 'runtime/native-build/build.json'
if record.exists():
    # PRoot keeps /proc/exe pointed at its ELF loader; mappings identify the app.
    assert '/runtime/native-build/build/lomiri-system-settings' in Path(f'/proc/{pid}/maps').read_text()
    print('PASS: native frontend uses the private build with upstream null guards')
print('PASS: real native binary, owned process group and private profile')
manager.StartTransientUnit(name, 'replace', [
    ('Environment', dbus.Array(['APP_ID=lomiri-system-settings'], signature='s')),
    ('ExecStart', dbus.Array([('/usr/bin/lomiri-system-settings',
                              dbus.Array(['/usr/bin/lomiri-system-settings'], signature='s'), False)],
                            signature='(sasb)')),
], [])
assert units()[name] == pid
print('PASS: repeat launch keeps the same native PID')
manager.StopUnit(name, 'replace')
for _ in range(40):
    if name not in units():
        break
    time.sleep(.2)
assert name not in units(), 'Native Settings did not stop'
assert units() == others, 'An unrelated app changed while stopping native Settings'
print('PASS: stop closes only native Settings; other app PIDs unchanged')
subprocess.run(['/usr/bin/lomiri-app-launch', 'lomiri-system-settings'],
               env=env, check=True, timeout=15)
time.sleep(2)
assert units()[name] != pid
print('PASS: native Settings opens again after an owned stop')
