#!/usr/bin/env python3
"""Bounded renderer probes on a separate Termux:X11 display; no session edits."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('backend', choices=['software', 'virgl', 'kgsl', 'zink'])
parser.add_argument('--angle', choices=['default', 'gl', 'vulkan'], default='default')
parser.add_argument('--display', default=':3')
args = parser.parse_args()
root = Path(__file__).resolve().parent.parent
runtime = root / 'runtime/gpu-experiments'
runtime.mkdir(parents=True, exist_ok=True)
guest_root = '/home/dev/gpu-experiments'
label = args.backend + ('-' + args.angle if args.backend == 'virgl' else '')
processes = []


def identity(pid):
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
    return fields[19], int(fields[2])


def start(command, name, env=None):
    with (runtime / name).open('w') as log:
        process = subprocess.Popen(command, env=env, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
    processes.append((process, identity(process.pid)[0]))
    return process


def stop(process, stamp):
    if process.poll() is not None:
        return
    try:
        if identity(process.pid) != (stamp, process.pid):
            raise RuntimeError(f'Process ownership changed: {process.pid}')
        os.killpg(process.pid, signal.SIGTERM)
        try:
            process.wait(timeout=3)
        except subprocess.TimeoutExpired:
            if identity(process.pid) == (stamp, process.pid):
                os.killpg(process.pid, signal.SIGKILL)
                process.wait(timeout=3)
    except FileNotFoundError:
        pass


try:
    host_env = os.environ.copy()
    host_env['DISPLAY'] = args.display
    if subprocess.run(['xrandr', '--current'], env=host_env,
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
        raise RuntimeError(f'Display {args.display} is already in use')
    xserver = start(['termux-x11', args.display, '-tag', 'lomiri-gpu-probe',
                     '-nolisten', 'tcp'], label + '-x11.log')
    for _ in range(40):
        if subprocess.run(['xrandr', '--current'], env=host_env,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            break
        if xserver.poll() is not None:
            raise RuntimeError('Probe X server exited')
        time.sleep(.25)
    else:
        raise RuntimeError('Probe X display did not become ready')
    variables = {'DISPLAY': args.display}
    if args.backend == 'software':
        variables.update(LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe')
    elif args.backend == 'virgl':
        host_socket = runtime / 'virgl.sock'
        if host_socket.exists():
            host_socket.unlink()
        command = ['virgl_test_server_android', '--no-fork', '--socket-path', str(host_socket)]
        if args.angle != 'default':
            command += ['--angle-' + args.angle]
        server = start(command, label + '-server.log')
        for _ in range(40):
            if host_socket.exists():
                break
            if server.poll() is not None:
                raise RuntimeError('VirGL server exited')
            time.sleep(.1)
        variables.update(GALLIUM_DRIVER='virpipe',
                         VTEST_SOCKET_NAME=guest_root + '/virgl.sock')
    else:
        library = guest_root + '/kgsl-root/usr/lib/aarch64-linux-gnu'
        variables.update(LD_LIBRARY_PATH=library, LIBGL_DRIVERS_PATH=library + '/dri',
                         __EGL_VENDOR_LIBRARY_FILENAMES=guest_root + '/kgsl-root/usr/share/glvnd/egl_vendor.d/50_mesa.json',
                         MESA_LOADER_DRIVER_OVERRIDE='kgsl' if args.backend == 'kgsl' else 'zink',
                         VK_DRIVER_FILES=guest_root + '/freedreno-private.json')
    login = ['proot-distro', 'login', 'lomiri-debian', '--user', 'dev', '--shared-tmp',
             '--bind', str(runtime) + ':' + guest_root, '--', '/usr/bin/env',
             '-u', 'LIBGL_ALWAYS_SOFTWARE', '-u', 'GALLIUM_DRIVER']
    login += [f'{key}={value}' for key, value in variables.items()]
    summary = {}
    for name, command in [('glx', ['glxinfo', '-B']), ('egl', ['eglinfo', '-B', '-p', 'x11'])]:
        filename = label + '-' + name + '.log'
        process = start(login + command, filename)
        try:
            code = process.wait(timeout=25)
        except subprocess.TimeoutExpired:
            stop(process, processes[-1][1])
            code = 'timeout'
        summary[name] = code
        print(filename, 'exit', code, (runtime / filename).read_text(errors='replace')[-5000:], flush=True)
    if args.backend == 'virgl':
        print('server:', (runtime / (label + '-server.log')).read_text(errors='replace')[-4000:], flush=True)
    (runtime / (label + '-summary.json')).write_text(json.dumps(summary, indent=2))
finally:
    for process, stamp in reversed(processes):
        stop(process, stamp)
