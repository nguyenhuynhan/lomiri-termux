#!/usr/bin/env python3
"""Run UniKey on this session's bus and forward focus metadata, never text."""
import json
import hashlib
import os
from pathlib import Path
import signal
import socket
import struct
import subprocess
import time

import dbus
from dbus.mainloop.glib import DBusGMainLoop
from dbus.lowlevel import MESSAGE_TYPE_METHOD_CALL
from gi.repository import Gio, GLib

ROOT = Path(__file__).resolve().parent.parent
RUNTIME = ROOT / 'runtime'
NAME = 'org.fcitx.Fcitx5'
CONTEXT = 'org.fcitx.Fcitx.InputContext1'


def main():
    owner = json.loads((RUNTIME / 'session.json').read_text())
    if os.getpgrp() != owner['pid']:
        raise RuntimeError('Keyboard must belong to the owned Lomiri process group')
    build = json.loads((RUNTIME / 'keyboard-build.json').read_text())
    version = subprocess.check_output(['dpkg-query', '-W', '-f=${Version}', 'libfcitx5core7'], text=True)
    binary = RUNTIME / 'keyboard-addons/liblomirikeyboardfocus.so'
    if (build['core_version'] != version
            or build['binary_sha256'] != hashlib.sha256(binary.read_bytes()).hexdigest()
            or build['source_sha256'] != hashlib.sha256((ROOT / 'src/keyboard-focus.cpp').read_bytes()).hexdigest()):
        raise RuntimeError('Keyboard addon changed; run scripts/install-keyboard.sh to rebuild it')
    DBusGMainLoop(set_as_default=True)
    bus = dbus.SessionBus()
    if bus.name_has_owner(NAME):
        raise RuntimeError('An input method already owns the private session bus')
    settings = Gio.Settings.new('com.lomiri.Termux')
    env = os.environ.copy()
    for key in ('DISPLAY', 'LD_PRELOAD', 'LD_LIBRARY_PATH'):
        env.pop(key, None)
    env['WAYLAND_DISPLAY'] = 'wayland-0'
    env['XDG_SESSION_TYPE'] = 'wayland'
    env['FCITX_ADDON_DIRS'] = str(RUNTIME / 'keyboard-addons') + ':/usr/lib/aarch64-linux-gnu/fcitx5'
    events_path = RUNTIME / 'keyboard-events.sock'
    events_path.unlink(missing_ok=True)
    events = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    events.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    events.bind(str(events_path))
    events_path.chmod(0o600)
    events_inode = events_path.stat().st_ino
    env['LOMIRI_KEYBOARD_EVENT_SOCKET'] = str(events_path)
    env['PATH'] = '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
    log = (RUNTIME / 'keyboard-ime.log').open('w')
    process = subprocess.Popen(
        ['/usr/bin/fcitx5', '-D', '--keep', '--disable=all',
         '--option=wayland=nodefault',
         '--enable=keyboard,unikey,dbus,dbusfrontend,ibusfrontend,wayland,waylandim,lomirikeyboardfocus'],
        env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT)
    core_focused = False
    outgoing = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    outgoing.setblocking(False)
    loop = GLib.MainLoop()
    sequence = 0
    clearing = None
    ready = RUNTIME / 'keyboard.ready'
    marker = {'pid': os.getpid(), 'owner_pid': owner['pid'], 'fcitx_pid': process.pid}

    def publish(show_request=False):
        nonlocal sequence
        sequence += 1
        enabled = core_focused
        payload = dict(marker, sequence=sequence, focused=enabled,
                       auto=settings.get_boolean('auto-keyboard'), show_request=show_request)
        try:
            outgoing.sendto(json.dumps(payload).encode(), str(RUNTIME / 'keyboard.sock'))
        except (FileNotFoundError, ConnectionRefusedError, BlockingIOError):
            pass

    def set_mode():
        subprocess.run(['/usr/bin/fcitx5-remote', '-o' if settings.get_boolean('vietnamese-input') else '-c'],
                       env=env, check=True, timeout=3, stdout=subprocess.DEVNULL)

    def changed(_settings, key):
        if key == 'vietnamese-input':
            set_mode()
        if key in ('vietnamese-input', 'auto-keyboard'):
            publish()

    def publish_focus(force):
        nonlocal clearing
        clearing = None
        publish(force)
        return False

    def core_event(_fd, _condition):
        nonlocal core_focused, clearing
        payload, ancillary, flags, _address = events.recvmsg(512, socket.CMSG_SPACE(12))
        credentials = next((struct.unpack('3i', data) for level, kind, data in ancillary
                            if level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS), None)
        try:
            event = json.loads(payload)
            if not credentials or credentials[0] != process.pid or flags & socket.MSG_TRUNC:
                return True
            if type(event.get('vietnamese')) is bool:
                if settings.get_boolean('vietnamese-input') != event['vietnamese']:
                    settings.set_boolean('vietnamese-input', event['vietnamese'])
                return True
            if type(event.get('focused')) is not bool or type(event.get('request')) is not bool:
                return True
            core_focused = event['focused']
            if clearing is not None:
                GLib.source_remove(clearing)
            clearing = GLib.timeout_add(100, publish_focus, event['request'])
        except (ValueError, KeyError, TypeError):
            pass
        return True

    def message(_connection, incoming):
        if (incoming.get_type() != MESSAGE_TYPE_METHOD_CALL
                or incoming.get_interface() != CONTEXT
                or incoming.get_destination() not in (NAME, fcitx_owner)):
            return
        if incoming.get_member() == 'ShowVirtualKeyboard':
            GLib.timeout_add(60, lambda: (publish(True), False)[1])

    def stop(_signum=None, _frame=None):
        loop.quit()

    def check_process():
        if process.poll() is not None:
            stop()
            return False
        return True

    wayland_opened = False
    controller = None

    def open_wayland():
        nonlocal wayland_opened
        if process.poll() is not None:
            return False
        if not wayland_opened and (Path(env['XDG_RUNTIME_DIR']) / 'wayland-0').exists():
            try:
                controller.OpenWaylandConnection('wayland-0', timeout=3)
            except dbus.DBusException:
                return True
            wayland_opened = True
            print('Input method connected to the owned Wayland compositor.', flush=True)
        return not wayland_opened

    monitor = None
    try:
        for _ in range(100):
            if bus.name_has_owner(NAME):
                break
            if process.poll() is not None:
                raise RuntimeError('Fcitx exited during startup; inspect keyboard-ime.log')
            time.sleep(.05)
        if not bus.name_has_owner(NAME):
            raise RuntimeError('Fcitx did not acquire its private bus name')
        fcitx_owner = str(bus.get_name_owner(NAME))
        monitor = dbus.bus.BusConnection(os.environ['DBUS_SESSION_BUS_ADDRESS'])
        monitor.add_message_filter(message)
        monitor.call_blocking('org.freedesktop.DBus', '/org/freedesktop/DBus',
                              'org.freedesktop.DBus.Monitoring', 'BecomeMonitor', 'asu',
                              ([f"type='method_call',interface='{CONTEXT}',member='ShowVirtualKeyboard'"], 0))
        controller = dbus.Interface(bus.get_object(NAME, '/controller'), 'org.fcitx.Fcitx.Controller1')
        GLib.io_add_watch(events.fileno(), GLib.IO_IN, core_event)
        GLib.timeout_add(500, open_wayland)
        settings.connect('changed', changed)
        set_mode()
        ready.write_text(json.dumps(marker))
        ready.chmod(0o600)
        signal.signal(signal.SIGTERM, stop)
        signal.signal(signal.SIGINT, stop)
        GLib.timeout_add_seconds(2, check_process)
        publish()
        print('UniKey ready; observing input focus only.', flush=True)
        loop.run()
    finally:
        core_focused = False
        publish()
        if ready.exists() and json.loads(ready.read_text()) == marker:
            ready.unlink()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print('Fcitx did not exit; session cleanup owns its process group.', flush=True)
        if monitor is not None:
            monitor.close()
        outgoing.close()
        events.close()
        if events_path.exists() and events_path.stat().st_ino == events_inode:
            events_path.unlink()
        log.close()


if __name__ == '__main__':
    main()
