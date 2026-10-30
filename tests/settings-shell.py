#!/usr/bin/env python3
"""Load the complete private shell overlay on Xvfb without restarting the phone UI.

Requires Xvfb in the guest. The probe owns a separate display, DBus bus, profile
and process groups. It tests QML startup, not touch, app launch or visible rotation.
"""
import os
from pathlib import Path
import signal
import subprocess
import tempfile
import time

root = Path(__file__).resolve().parent.parent


def identity(pid):
    return Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()[19]


def stop_owned(process, started):
    if process.poll() is not None:
        return
    assert os.getpgid(process.pid) == process.pid and identity(process.pid) == started
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        assert os.getpgid(process.pid) == process.pid and identity(process.pid) == started
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=5)


with tempfile.TemporaryDirectory(prefix='settings-shell-', dir=root / 'runtime') as folder:
    probe = Path(folder)
    env = os.environ.copy()
    for key in ('DBUS_SESSION_BUS_ADDRESS', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'WAYLAND_DISPLAY', 'MIR_SOCKET'):
        env.pop(key, None)
    for key, suffix in [('XDG_RUNTIME_DIR', 'xdg'), ('XDG_CONFIG_HOME', 'config'),
                        ('XDG_DATA_HOME', 'data'), ('XDG_CACHE_HOME', 'cache')]:
        target = probe / suffix
        target.mkdir(mode=0o700)
        env[key] = str(target)
    env.update(QT_QPA_PLATFORM='mirserver', GRID_UNIT_PX='8', QSG_RENDER_LOOP='basic',
               LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe',
               MIR_SERVER_CONSOLE_PROVIDER='none', MIR_SERVER_X11_OUTPUT='672x1339',
               GSETTINGS_SCHEMA_DIR=str(root / 'runtime/data/glib-2.0/schemas'),
               XDG_CURRENT_DESKTOP='Lomiri', HOME=str(probe))
    with (probe / 'display').open('w') as display, (probe / 'xvfb.log').open('w') as xvfb_log:
        xvfb = subprocess.Popen(['Xvfb', '-displayfd', str(display.fileno()), '-screen', '0',
                                 '672x1339x24', '-nolisten', 'tcp'], pass_fds=(display.fileno(),),
                                stdout=xvfb_log, stderr=xvfb_log, start_new_session=True)
        xvfb_start = identity(xvfb.pid)
        shell = None
        try:
            for _ in range(50):
                if (probe / 'display').read_text().strip():
                    break
                assert xvfb.poll() is None, (probe / 'xvfb.log').read_text()
                time.sleep(.1)
            number = (probe / 'display').read_text().strip()
            assert number.isdigit(), 'Xvfb did not report a private display'
            env['DISPLAY'] = ':' + number
            log = root / 'runtime/settings-shell-probe.log'
            with log.open('w') as output:
                shell = subprocess.Popen(['dbus-run-session', '--', 'lomiri', '--mode=shell',
                                          '--qmlfile=' + str(root / 'runtime/host-qml/ShellApplication.qml')],
                                         env=env, stdout=output, stderr=subprocess.STDOUT,
                                         start_new_session=True)
                shell_start = identity(shell.pid)
                for _ in range(200):
                    text = log.read_text(errors='replace')
                    if 'LOMIRI_SHELL_READY' in text:
                        break
                    if shell.poll() is not None:
                        raise AssertionError(text[-6000:])
                    time.sleep(.1)
                assert 'LOMIRI_SHELL_READY' in text, text[-6000:]
                time.sleep(2)
                assert shell.poll() is None, log.read_text(errors='replace')[-6000:]
                text = log.read_text(errors='replace')
                failures = [line for line in text.splitlines() if any(s in line for s in (
                    'is not a type', 'Cannot assign', 'ReferenceError:', 'TypeError:',
                    'Binding loop detected', 'Component is not ready', 'is not installed'))]
                assert not failures, '\n'.join(failures)
                print('PASS: complete Settings shell overlay ready on a private Xvfb display')
                print('Log:', log)
        finally:
            if shell is not None:
                stop_owned(shell, shell_start)
            stop_owned(xvfb, xvfb_start)
