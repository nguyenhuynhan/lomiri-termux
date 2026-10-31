#!/usr/bin/env python3
"""Run a bounded Lomiri GPU experiment from a private project copy."""
import argparse
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('backend', choices=['software', 'virgl', 'kgsl', 'zink'])
parser.add_argument('--duration', type=int, default=90)
parser.add_argument('--render-loop', choices=['basic', 'threaded'], default='basic')
parser.add_argument('--client-backend', choices=['inherit', 'kgsl', 'software'], default='inherit')
parser.add_argument('--trace-input', action='store_true')
parser.add_argument('--trace-crash', action='store_true')
parser.add_argument('--timing', action='store_true')
parser.add_argument('--exercise-menu', action='store_true')
args = parser.parse_args()
if args.client_backend == 'kgsl' and args.backend not in ['kgsl', 'zink']:
    parser.error('--client-backend kgsl requires a kgsl or zink shell')
label = args.backend + ('-threaded' if args.render_loop == 'threaded' else '')
root = Path(__file__).resolve().parent.parent
experiment = root / 'runtime/gpu-experiments'
# PRoot translates Unix socket paths to the host path. Keep that path short
# enough for clients started through a separate PRoot invocation.
project = root / 'runtime' / ('gpu-' + args.backend)
guest = '/home/dev/projects/lomiri-gpu-' + args.backend
lib = '/home/dev/gpu-experiments/kgsl-root/usr/lib/aarch64-linux-gnu'
env = os.environ.copy()
env.update(LOMIRI_DIRECT='1', LOMIRI_DISPLAY=':3', LOMIRI_X11_OUTPUT='672x1339',
           LOMIRI_SOFTWARE_RENDERING='1' if args.backend == 'software' else '0',
           LOMIRI_MOUSE_COMPAT='1', LOMIRI_INPUT_TRACE='1' if args.trace_input else '0',
           LOMIRI_TRACE='1' if args.trace_crash else '0')
env['LOMIRI_CODE_NO_SANDBOX'] = subprocess.check_output(
    ['bash', '-c', 'source scripts/common.sh; printf "%s" "$LOMIRI_CODE_NO_SANDBOX"'],
    cwd=root, text=True).strip()
for key in ['LIBGL_ALWAYS_SOFTWARE', 'GALLIUM_DRIVER', 'LD_LIBRARY_PATH',
            'MESA_LOADER_DRIVER_OVERRIDE', 'VK_DRIVER_FILES']:
    env.pop(key, None)
if subprocess.run(['xrandr', '--current'], env={**env, 'DISPLAY': ':3'},
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Probe display :3 is busy')
project.mkdir(parents=True, exist_ok=True)
if (project / 'runtime/session.json').exists():
    old = json.loads((project / 'runtime/session.json').read_text())
    if Path(f'/proc/{old["pid"]}').exists():
        raise SystemExit('Existing experiment session must finish first')
for folder in ['scripts', 'src', 'apps']:
    shutil.copytree(root / folder, project / folder, dirs_exist_ok=True)
(project / 'runtime').mkdir(exist_ok=True)
for name in ['input-compat.json', 'libqt-mouse-dispatch-compat.so']:
    shutil.copy2(root / 'runtime' / name, project / 'runtime' / name)
if args.trace_input and (root / 'runtime/libqt-input-probe.so').exists():
    shutil.copy2(root / 'runtime/libqt-input-probe.so', project / 'runtime/libqt-input-probe.so')
if args.trace_crash:
    shutil.copy2(root / 'runtime/libcrash-trace.so', project / 'runtime/libcrash-trace.so')
for relative in ['config/dconf/user', 'config/lomiri-ui-toolkit/theme.ini',
                 'core-launcher-v1', 'settings-launcher-v1']:
    source = root / 'runtime' / relative
    destination = project / 'runtime' / relative
    if source.exists() and not destination.exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)

path = project / 'scripts/common.sh'
text = path.read_text().replace('LOMIRI_GUEST_ROOT=/home/dev/projects/lomiri-termux',
                                'LOMIRI_GUEST_ROOT=' + guest)
text = text.replace('--bind "$PROJECT_ROOT:$LOMIRI_GUEST_ROOT"',
                    '--bind "$PROJECT_ROOT:$LOMIRI_GUEST_ROOT" --bind "' + str(experiment) + ':/home/dev/gpu-experiments"')
path.write_text(text)
path = project / 'scripts/session.sh'
text = path.read_text().replace('lomiri-poc', 'lomiri-gpu-probe')
path.write_text(text)
path = project / 'scripts/guest-session.sh'
text = path.read_text().replace('export QSG_RENDER_LOOP=basic',
                                'export QSG_RENDER_LOOP=' + args.render_loop)
renderer = 'export QSG_INFO=1\n'
if args.timing:
    renderer += 'export QSG_RENDER_TIMING=1\n'
if args.backend == 'virgl':
    renderer += 'export GALLIUM_DRIVER=virpipe\nexport VTEST_SOCKET_NAME=/home/dev/gpu-experiments/virgl.sock\n'
elif args.backend in ['kgsl', 'zink']:
    renderer += ('export LD_LIBRARY_PATH=' + lib + '\nexport LIBGL_DRIVERS_PATH=' + lib + '/dri\n'
                 'export __EGL_VENDOR_LIBRARY_FILENAMES=/home/dev/gpu-experiments/kgsl-root/usr/share/glvnd/egl_vendor.d/50_mesa.json\n'
                 'export MESA_LOADER_DRIVER_OVERRIDE=' + ('kgsl' if args.backend == 'kgsl' else 'zink') + '\n'
                 'export VK_DRIVER_FILES=/home/dev/gpu-experiments/freedreno-private.json\n')
text = text.replace('unset DBUS_SESSION_BUS_ADDRESS', renderer + 'unset DBUS_SESSION_BUS_ADDRESS')
path.write_text(text)
path = project / 'scripts/guest-app-services.py'
text = path.read_text().replace("host = '/data/data/com.termux/files/home/projects/lomiri-termux'",
                                'host = ' + repr(str(project)))
path.write_text(text)
if args.backend != 'software':
    path = project / 'scripts/guest-app-services.py'
    text = path.read_text().replace("'LD_LIBRARY_PATH', ", '')
    text = text.replace("LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe'", "LOMIRI_GPU_EXPERIMENT='1'")
    if args.client_backend != 'software':
        text = text.replace("'--disable-gpu', ", '')
    if args.client_backend == 'kgsl':
        text = text.replace("        home = RUNTIME / 'app-home'",
                            "        env['MESA_LOADER_DRIVER_OVERRIDE'] = 'kgsl'\n"
                            "        home = RUNTIME / 'app-home'")
    elif args.client_backend == 'software':
        text = text.replace("        home = RUNTIME / 'app-home'",
                            "        env.update(LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe', "
                            "MESA_LOADER_DRIVER_OVERRIDE='swrast')\n"
                            "        home = RUNTIME / 'app-home'")
    path.write_text(text)
    path = project / 'scripts/guest-settings.py'
    text = path.read_text().replace("'LD_LIBRARY_PATH', ", '')
    text = text.replace("LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe'", "LOMIRI_GPU_EXPERIMENT='1'")
    path.write_text(text)
    path = project / 'scripts/prepare-host-shell.py'
    text = path.read_text()
    if args.client_backend != 'software':
        text = text.replace("'terminal.integrated.gpuAcceleration': 'off'", "'terminal.integrated.gpuAcceleration': 'auto'")
    path.write_text(text)

processes = []
def stamp(pid):
    f = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
    return f[19], int(f[2])
def spawn(command, logfile):
    with (experiment / logfile).open('w') as log:
        p = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
                             stdout=log, stderr=subprocess.STDOUT, start_new_session=True)
    processes.append((p, stamp(p.pid)[0]))
    return p
try:
    if args.backend == 'virgl':
        socket = experiment / 'virgl.sock'
        if socket.exists():
            socket.unlink()
        spawn(['virgl_test_server_android', '--no-fork', '--socket-path', str(socket)], 'virgl-shell-server.log')
        time.sleep(1)
    session = spawn(['bash', str(project / 'scripts/session.sh')], label + '-shell.log')
    (experiment / 'active.json').write_text(json.dumps({'backend': args.backend, 'pid': session.pid,
        'stamp': processes[-1][1], 'project': str(project), 'guest': guest}))
    print('Experiment session', args.backend, session.pid, 'duration', args.duration, flush=True)
    if args.exercise_menu:
        for _ in range(100):
            content = (experiment / (label + '-shell.log')).read_text(errors='replace')
            if 'GL_RENDERER:' in content:
                break
            if session.poll() is not None:
                raise RuntimeError('Shell failed before menu exercise')
            time.sleep(.2)
        else:
            raise RuntimeError('Renderer initialization timed out')
        display_env = {**env, 'DISPLAY': ':3'}
        time.sleep(2)
        for _ in range(2):
            subprocess.run(['xdotool', 'mousemove', '25', '1305', 'mousedown', '1',
                            'sleep', '.15', 'mouseup', '1'], env=display_env, check=True)
            time.sleep(1.5)
        start_offset = (experiment / (label + '-shell.log')).stat().st_size
        print('Beginning 12 menu toggles', flush=True)
        for i in range(12):
            subprocess.run(['xdotool', 'mousemove', '25', '1305', 'mousedown', '1',
                            'sleep', '.15', 'mouseup', '1'], env=display_env, check=True)
            time.sleep(1.1)
        print('Menu exercise completed', flush=True)
        recorded = (experiment / (label + '-shell.log')).read_bytes()[start_offset:]
        (experiment / (label + '-menu-timing.log')).write_bytes(recorded)
        print('Experiment shell log', experiment / (label + '-shell.log'), flush=True)
        args.duration = 1
    try:
        code = session.wait(timeout=args.duration)
        print('Experiment session exited', code, flush=True)
    except subprocess.TimeoutExpired:
        print('Experiment duration completed', flush=True)
finally:
    for p, token in reversed(processes):
        if p.poll() is not None:
            continue
        try:
            if stamp(p.pid) == (token, p.pid):
                os.killpg(p.pid, signal.SIGTERM)
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    if stamp(p.pid) == (token, p.pid):
                        os.killpg(p.pid, signal.SIGKILL)
                        p.wait(timeout=3)
        except FileNotFoundError:
            pass
    # A supervisor that exits during startup can leave a broker behind. Verify
    # both the recorded group and this experiment's command path before signals.
    for process, _ in processes:
        for entry in Path('/proc').iterdir():
            if not entry.name.isdigit():
                continue
            try:
                token, group = stamp(int(entry.name))
                command = (entry / 'cmdline').read_bytes().replace(b'\0', b' ').decode(errors='replace')
                belongs = str(project) in command or guest + '/' in command
                belongs = belongs or ('termux-x11' in command and '-tag lomiri-gpu-probe' in command)
                if group == process.pid and belongs and stamp(int(entry.name)) == (token, group):
                    os.kill(int(entry.name), signal.SIGTERM)
            except (FileNotFoundError, ProcessLookupError, PermissionError):
                pass
