#!/usr/bin/env python3
"""Live Settings probe: reject Python misuse, launch once and stop only our app.

Run in the selected guest after restarting Lomiri. Refuses to close an already
running Settings app. Other applications remain running throughout the probe.
"""
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


def settings_units():
    return [u for u in manager.ListUnits() if '--lomiri-session-settings--' in str(u[0])]


assert not settings_units(), 'Close Settings before running this probe'
others = {str(u[0]): str(u[6]) for u in manager.ListUnits()}
name = 'lomiri-app-launch--application-legacy--lomiri-session-settings--.service'
for binary, arguments in [('/usr/bin/python3', ['/usr/bin/python3', '-c', 'raise SystemExit(99)']),
                           ('/usr/bin/bash', ['/usr/bin/bash', str(root / 'scripts/guest-settings.py')])]:
    try:
        manager.StartTransientUnit(name, 'replace', [
            ('Environment', dbus.Array(['APP_ID=lomiri-session-settings'], signature='s')),
            ('ExecStart', dbus.Array([(binary, dbus.Array(arguments, signature='s'), False)], signature='(sasb)')),
        ], [])
        raise AssertionError('Settings must reject arbitrary executables or Python arguments')
    except dbus.DBusException as error:
        assert error.get_dbus_name() == 'org.freedesktop.systemd1.NotSupported'
print('PASS: arbitrary Settings executables and Python arguments rejected')
try:
    subprocess.run(['/usr/bin/lomiri-app-launch', 'lomiri-session-settings'],
                   env=env, check=True, timeout=15)
    time.sleep(2)
    # Exercise the adapter's duplicate request without UAL's unsupported
    # standalone-client resume handshake. The dock focuses existing windows.
    manager.StartTransientUnit(name, 'replace', [
        ('Environment', dbus.Array(['APP_ID=lomiri-session-settings'], signature='s')),
        ('ExecStart', dbus.Array([('/usr/bin/python3', dbus.Array([
            '/usr/bin/python3', str(root / 'scripts/guest-settings.py')], signature='s'), False)],
            signature='(sasb)')),
    ], [])
    time.sleep(1)
    units = settings_units()
    assert len(units) == 1, 'Settings must be single-instance'
    props = dbus.Interface(bus.get_object('org.freedesktop.systemd1', units[0][6]),
                           'org.freedesktop.DBus.Properties')
    pid = int(props.Get('org.freedesktop.systemd1.Service', 'MainPID'))
    owner = json.loads((root / 'runtime/session.json').read_text())['pid']
    assert os.getpgid(pid) == owner
    command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    assert str(root / 'apps/SessionSettings.qml').encode() in command
    assert Path(env['GSETTINGS_SCHEMA_DIR']).resolve() == root / 'runtime/data/glib-2.0/schemas'
    print('PASS: one QML Settings client, owned process group and private schemas')
finally:
    for unit in settings_units():
        manager.StopUnit(unit[0], 'replace')
    for _ in range(30):
        if not settings_units():
            break
        time.sleep(.2)
    assert not settings_units(), 'Settings did not exit'
    current = {str(u[0]): str(u[6]) for u in manager.ListUnits()}
    assert all(current.get(name) == path for name, path in others.items())
    print('PASS: Settings stopped; other application units preserved')
