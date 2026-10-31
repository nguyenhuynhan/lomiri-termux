#!/usr/bin/env python3
"""Private app-launch adapter for PRoot, implementing only UAL's unit protocol.

This is not a systemd replacement: it starts a bounded list of GUI applications
on this session's bus, keeps them in the owned process group, and reports their
real PIDs/exits. No host services or cgroups are changed.
"""
import os
import json
import hashlib
from pathlib import Path
import runpy
import signal
import subprocess

import dbus
import dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / 'runtime'
MANAGER = 'org.freedesktop.systemd1.Manager'
SERVICE = 'org.freedesktop.systemd1.Service'
UNIT = 'org.freedesktop.systemd1.Unit'
PROPS = 'org.freedesktop.DBus.Properties'
BASE = '/org/freedesktop/systemd1'
ALLOWED = {
    'lomiri-terminal-app', 'lomiri-filemanager-app', 'lomiri-calculator-app',
    'lomiri-clock-app', 'lomiri-calendar-app', 'lomiri-gallery-app',
    'lomiri-mediaplayer-app', 'firefox-esr', 'com.microsoft.VSCode',
    'lomiri-code', 'lomiri-chatgpt', 'lomiri-session-settings', 'lomiri-system-settings',
}


class Rejected(dbus.DBusException):
    _dbus_error_name = 'org.freedesktop.systemd1.NotSupported'


class AppUnit(dbus.service.Object):
    def __init__(self, manager, name, process, env):
        self.manager, self.name, self.process = manager, name, process
        self.start_time = manager.identity(process.pid)
        self.env = env
        self.pid_directory = RUNTIME / 'app-pids' / hashlib.sha256(name.encode()).hexdigest()
        self.pid_directory.mkdir(parents=True, exist_ok=True)
        self.path = BASE + '/unit/' + ''.join(c if c.isascii() and c.isalnum()
                                             else f'_{ord(c):02x}' for c in name)
        super().__init__(manager.bus, self.path)

    def refresh_pids(self):
        # UAL supports a private PID registry root. These files are metadata,
        # not kernel cgroups: include only descendants in our verified group.
        parents = {}
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                pid = int(entry.name)
                fields = (entry / 'stat').read_text().rsplit(') ', 1)[1].split()
                if fields[0] != 'Z' and int(fields[2]) == self.manager.owner['pid']:
                    parents[pid] = int(fields[1])
            except (OSError, ValueError, IndexError):
                continue
        descendants = {self.process.pid} if self.process.poll() is None else set()
        while True:
            added = {pid for pid, parent in parents.items() if parent in descendants} - descendants
            if not added:
                break
            descendants.update(added)
        temporary = self.pid_directory / 'tasks.tmp'
        temporary.write_text(''.join(f'{pid}\n' for pid in sorted(descendants)))
        temporary.replace(self.pid_directory / 'tasks')

    @dbus.service.method(PROPS, in_signature='ss', out_signature='v')
    def Get(self, interface, name):
        values = self.GetAll(interface)
        if name not in values:
            raise Rejected(f'Unsupported property {interface}.{name}')
        return values[name]

    @dbus.service.method(PROPS, in_signature='s', out_signature='a{sv}')
    def GetAll(self, interface):
        alive = self.process.poll() is None
        if interface == SERVICE:
            self.refresh_pids()
            return {'MainPID': dbus.UInt32(self.process.pid if alive else 0),
                    'ControlGroup': dbus.String(self.pid_directory.name),
                    'Environment': dbus.Array([f'{k}={v}' for k, v in self.env.items()], signature='s'),
                    'Result': dbus.String('success' if alive or self.process.returncode == 0 else 'exit-code')}
        if interface == UNIT:
            return {'Id': dbus.String(self.name), 'ActiveState': dbus.String('active' if alive else 'inactive'),
                    'SubState': dbus.String('running' if alive else 'dead')}
        raise Rejected(f'Unsupported interface {interface}')

    @dbus.service.signal(PROPS, signature='sa{sv}as')
    def PropertiesChanged(self, interface, changed, invalidated):
        pass

    def stop(self):
        if self.process.poll() is None and self.manager.identity(self.process.pid) == self.start_time:
            self.process.terminate()


class AppServices(dbus.service.Object):
    def __init__(self, bus):
        state = runpy.run_path(str(ROOT / 'scripts/session-state.py'))
        self.identity = state['identity']
        self.owner = self.active()
        if os.getpgrp() != self.owner['pid']:
            raise RuntimeError('App services must belong to the owned Lomiri process group')
        self.bus, self.units, self.jobs = bus, {}, 0
        self.name = dbus.service.BusName('org.freedesktop.systemd1', bus, do_not_queue=True)
        super().__init__(bus, BASE)

    def active(self):
        # The bind mount has a different path inside PRoot; validate the host
        # record and host command line rather than comparing it to guest ROOT.
        owner = json.loads((RUNTIME / 'session.json').read_text())
        pid = owner['pid']
        host = '/data/data/com.termux/files/home/projects/lomiri-termux'
        command = Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
        if (owner['project'] != host or self.identity(pid) != owner['start_time']
                or os.getpgid(pid) != pid or (host + '/scripts/session.sh').encode() not in command):
            raise RuntimeError('Stale or unrelated session identity')
        return owner

    @dbus.service.method(MANAGER, in_signature='', out_signature='')
    def Subscribe(self):
        pass

    @dbus.service.method(MANAGER, in_signature='', out_signature='a(ssssssouso)')
    def ListUnits(self):
        return [(name, name, 'loaded', 'active', 'running', '', unit.path, 0, '', '/')
                for name, unit in self.units.items() if unit.process.poll() is None]

    @dbus.service.method(MANAGER, in_signature='s', out_signature='o')
    def GetUnit(self, name):
        if name not in self.units:
            raise Rejected(f'Unknown application unit {name}')
        return self.units[name].path

    @dbus.service.method(MANAGER, in_signature='ssa(sv)a(sa(sv))', out_signature='o')
    def StartTransientUnit(self, name, mode, properties, auxiliary):
        if self.active() != self.owner or not name.startswith('lomiri-app-launch--') or auxiliary:
            raise Rejected('Only application units inside the owned session are supported')
        if name in self.units and self.units[name].process.poll() is None:
            return self.new_job(name)
        props = dict(properties)
        requested = dict(str(item).split('=', 1) for item in props.get('Environment', []))
        app = requested.get('APP_ID', '')
        commands = props.get('ExecStart', [])
        if app not in ALLOWED or len(commands) != 1:
            raise Rejected(f'Application is not enabled for this PRoot session: {app}')
        binary, arguments, _ = commands[0]
        args = [str(arg) for arg in arguments]
        resolved = Path(str(binary)).resolve()
        expected = {
            'com.microsoft.VSCode': '/usr/share/code/code', 'lomiri-code': '/usr/share/code/code',
            'firefox-esr': '/usr/bin/firefox-esr', 'lomiri-chatgpt': '/usr/bin/firefox-esr',
            'lomiri-session-settings': '/usr/bin/python3',
        }.get(app, '/usr/bin/' + app)
        if resolved != Path(expected).resolve():
            raise Rejected(f'Unexpected executable for {app}: {binary}')
        if app == 'lomiri-session-settings' and args != [str(binary), str(ROOT / 'scripts/guest-settings.py')]:
            raise Rejected('Only the project Settings script is supported')
        env = os.environ.copy()
        env.update(requested)
        for key in ('DISPLAY', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'MIR_SOCKET', 'ELECTRON_RUN_AS_NODE'):
            env.pop(key, None)
        env.update(PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
                   QT_QPA_PLATFORM='wayland', QT_SCALE_FACTOR='1', QT_AUTO_SCREEN_SCALE_FACTOR='0',
                   QT_WAYLAND_DISABLE_WINDOWDECORATION='1', QT_FONT_DPI='96',
                   WAYLAND_DISPLAY='wayland-0', GDK_BACKEND='wayland', MOZ_ENABLE_WAYLAND='1',
                   LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe')
        home = RUNTIME / 'app-home'
        home.mkdir(mode=0o700, exist_ok=True)
        env['HOME'] = str(home)
        if app == 'lomiri-terminal-app':
            env['SHELL'] = '/bin/bash'
        launch_binary = str(binary)
        if app == 'lomiri-system-settings':
            env['XDG_DATA_DIRS'] = '/usr/local/share:/usr/share:' + str(RUNTIME / 'native-data')
            build_record = RUNTIME / 'native-build/build.json'
            frontend = RUNTIME / 'native-build/build/lomiri-system-settings'
            if build_record.exists():
                record = json.loads(build_record.read_text())
                if (record.get('source_version') != '1.3.1'
                        or hashlib.sha256(frontend.read_bytes()).hexdigest() != record.get('binary_sha256')
                        or hashlib.sha256(Path('/usr/bin/lomiri-system-settings').read_bytes()).hexdigest()
                           != record.get('packaged_binary_sha256')):
                    raise Rejected('Native Settings frontend build verification failed')
                launch_binary = str(frontend)
        if app in ('com.microsoft.VSCode', 'lomiri-code'):
            args = [str(binary), '--ozone-platform=wayland', '--disable-gpu', '--disable-dev-shm-usage',
                    f'--user-data-dir={RUNTIME / "vscode/user-data"}',
                    f'--extensions-dir={RUNTIME / "vscode/extensions"}', str(RUNTIME / 'code-workspace')]
            if env.get('GTK_IM_MODULE') == 'fcitx':
                args[1:1] = ['--enable-wayland-ime', '--wayland-text-input-version=1']
            if os.environ.get('LOMIRI_CODE_NO_SANDBOX') == '1':
                args.insert(1, '--no-sandbox')
        elif app in ('firefox-esr', 'lomiri-chatgpt'):
            args = [str(binary), '--no-remote', '--profile', str(RUNTIME / 'firefox-chatgpt'), 'https://chatgpt.com/']
        with (RUNTIME / f'app-{app}.log').open('a') as log:
            process = subprocess.Popen(args, executable=launch_binary, env=env, cwd=home,
                                       stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
        unit = AppUnit(self, str(name), process, env)
        self.units[str(name)] = unit
        print(f'Launched {app}: pid={process.pid}, unit={name}', flush=True)
        self.UnitNew(name, unit.path)
        return self.new_job(name)

    def new_job(self, name):
        self.jobs += 1
        path = BASE + f'/job/{self.jobs}'
        GLib.idle_add(self.JobRemoved, self.jobs, path, name, 'done')
        return path

    @dbus.service.method(MANAGER, in_signature='ss', out_signature='o')
    def StopUnit(self, name, mode):
        if name not in self.units:
            raise Rejected('Unknown application unit')
        self.units[name].stop()
        return self.new_job(name)

    @dbus.service.method(MANAGER, in_signature='s', out_signature='')
    def ResetFailedUnit(self, name):
        pass

    @dbus.service.signal(MANAGER, signature='so')
    def UnitNew(self, name, path):
        pass

    @dbus.service.signal(MANAGER, signature='so')
    def UnitRemoved(self, name, path):
        pass

    @dbus.service.signal(MANAGER, signature='uoss')
    def JobRemoved(self, number, path, name, result):
        pass

    def reap(self):
        for name, unit in list(self.units.items()):
            if unit.process.poll() is not None:
                print(f'Exited {name}: status={unit.process.returncode}', flush=True)
                unit.PropertiesChanged(SERVICE, {'Result': unit.Get(SERVICE, 'Result')}, [])
                self.UnitRemoved(name, unit.path)
                unit.remove_from_connection()
                del self.units[name]
        return True


if __name__ == '__main__':
    DBusGMainLoop(set_as_default=True)
    manager = AppServices(dbus.SessionBus())
    loop = GLib.MainLoop()
    def stop(*_):
        loop.quit()
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    GLib.timeout_add(500, manager.reap)
    (RUNTIME / 'app-services.ready').write_text(os.environ['DBUS_SESSION_BUS_ADDRESS'])
    try:
        loop.run()
    finally:
        for unit in manager.units.values():
            unit.stop()
        (RUNTIME / 'app-services.ready').unlink(missing_ok=True)
