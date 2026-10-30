#!/usr/bin/env python3
"""Live integration probe: UAL launches, PID metadata, duplicate requests and stop.

Run inside the selected guest after starting a clean Lomiri session. Uses only
the Calculator test app and refuses to close an already running Calculator.
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
def calculators():
    return [unit for unit in manager.ListUnits() if '--lomiri-calculator-app--' in unit[0]]
assert not calculators(), 'Close the test Calculator before running this probe'
try:
    manager.StartTransientUnit('unrelated.service', 'replace', [], [])
    raise AssertionError('Unrelated units must be rejected')
except dbus.DBusException as error:
    assert error.get_dbus_name() == 'org.freedesktop.systemd1.NotSupported'
unit = None
try:
    for _ in range(2):
        subprocess.run(['/usr/bin/lomiri-app-launch', 'lomiri-calculator-app'], env=env, check=True)
        time.sleep(1)
    records = calculators()
    # Calculator permits separate instances; each must have a real, distinct PID.
    assert records
    pids = set()
    for record in records:
        props = dbus.Interface(bus.get_object('org.freedesktop.systemd1', record[6]),
                               'org.freedesktop.DBus.Properties')
        pid = int(props.Get('org.freedesktop.systemd1.Service', 'MainPID'))
        assert pid > 0 and pid not in pids
        pids.add(pid)
        group = str(props.Get('org.freedesktop.systemd1.Service', 'ControlGroup'))
        tasks = (root / 'runtime/app-pids' / group / 'tasks').read_text().splitlines()
        assert str(pid) in tasks
        owner = json.loads((root / 'runtime/session.json').read_text())['pid']
        assert all(os.getpgid(int(child)) == owner for child in tasks)
    print('PASS: UAL launch, PID registry and rejection of unrelated services')
finally:
    for record in calculators():
        manager.StopUnit(record[0], 'replace')
    for _ in range(30):
        if not calculators():
            break
        time.sleep(.2)
    assert not calculators(), 'Test Calculator did not stop'
    print('PASS: owned application stop and real exit notification')
