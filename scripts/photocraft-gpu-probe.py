#!/usr/bin/env python3
"""Bounded PhotoCraft GPU probe on its own X11 display and empty profile."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time
import struct
import zlib

parser = argparse.ArgumentParser()
parser.add_argument('backend', choices=['gl', 'vulkan'])
parser.add_argument('--duration', type=int, default=30)
options = parser.parse_args()
root = Path(__file__).resolve().parent.parent
work = root / 'runtime/photocraft-gpu'
work.mkdir(parents=True, exist_ok=True)
guest = '/home/dev/projects/lomiri-termux'
lib = guest + '/runtime/gpu-experiments/kgsl-root/usr/lib/aarch64-linux-gnu'
images = sorted((root / 'runtime/app-home/Applications').glob('photocraft-*-linux-aarch64.AppImage'))
if not images:
    raise SystemExit('PhotoCraft AppImage is not installed')
display = ':4'
host_env = {**os.environ, 'DISPLAY': display}
if subprocess.run(['xrandr', '--current'], env=host_env,
                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
    raise SystemExit('Display :4 is already in use; leaving it alone')
processes = []


def identity(pid):
    fields = Path(f'/proc/{pid}/stat').read_text().rsplit(') ', 1)[1].split()
    return fields[19], int(fields[2])


def start(command, label):
    with (work / (label + '.log')).open('w') as log:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=log,
                                   stderr=subprocess.STDOUT, start_new_session=True)
    processes.append((process, identity(process.pid)))
    return process


try:
    server = start(['termux-x11', display, '-tag', 'photocraft-gpu-probe', '-nolisten', 'tcp'], 'x11')
    for _ in range(40):
        if subprocess.run(['xrandr', '--current'], env=host_env,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode == 0:
            break
        if server.poll() is not None:
            raise RuntimeError('Probe X11 server exited')
        time.sleep(.25)
    else:
        raise RuntimeError('Probe X11 did not become ready')
    prefix = guest + '/runtime/photocraft-gpu/' + options.backend
    for name in ['home', 'config', 'data', 'cache', 'xdg']:
        (work / options.backend / name).mkdir(parents=True, exist_ok=True)
    (work / options.backend / 'xdg').chmod(0o700)
    icd = work / 'freedreno.json'
    icd.write_text(json.dumps({'file_format_version': '1.0.1', 'ICD': {
        'library_path': lib + '/libvulkan_freedreno.so', 'api_version': '1.4.363'}}))
    env = {
        'DISPLAY': display, 'HOME': prefix + '/home', 'XDG_CONFIG_HOME': prefix + '/config',
        'XDG_DATA_HOME': prefix + '/data', 'XDG_CACHE_HOME': prefix + '/cache',
        'XDG_RUNTIME_DIR': prefix + '/xdg', 'WINIT_UNIX_BACKEND': 'x11',
        'WGPU_BACKEND': options.backend, 'APPIMAGE_EXTRACT_AND_RUN': '1',
        'PHOTOCRAFT_NO_DESKTOP_INTEGRATION': '1', 'PHOTOCRAFT_NEW_INSTANCE': '1',
        'LD_LIBRARY_PATH': lib, 'LIBGL_DRIVERS_PATH': lib + '/dri',
        '__EGL_VENDOR_LIBRARY_FILENAMES': guest + '/runtime/gpu-experiments/kgsl-root/usr/share/glvnd/egl_vendor.d/50_mesa.json',
        'MESA_LOADER_DRIVER_OVERRIDE': 'kgsl', 'VK_DRIVER_FILES': guest + '/runtime/photocraft-gpu/freedreno.json',
        'RUST_LOG': 'warn,photocraft*=info,wgpu_core=info,wgpu_hal=info',
    }
    sample = work / 'sample.png'
    def chunk(kind, content):
        return struct.pack('>I', len(content)) + kind + content + struct.pack('>I', zlib.crc32(kind + content))
    pixels = b''.join(b'\0' + bytes(value for x in range(256) for value in (x, y, 128, 255)) for y in range(256))
    sample.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 256, 256, 8, 6, 0, 0, 0))
                       + chunk(b'IDAT', zlib.compress(pixels)) + chunk(b'IEND', b''))
    login = ['proot-distro', 'login', 'lomiri-debian', '--user', 'dev', '--shared-tmp',
             '--bind', str(root) + ':' + guest, '--', '/usr/bin/env']
    for key in ['LIBGL_ALWAYS_SOFTWARE', 'GALLIUM_DRIVER', 'WAYLAND_DISPLAY', 'LD_PRELOAD', 'VK_ICD_FILENAMES', 'DBUS_SESSION_BUS_ADDRESS']:
        login += ['-u', key]
    login += [key + '=' + value for key, value in env.items()]
    client = start(login + [guest + '/runtime/app-home/Applications/' + images[-1].name,
                            guest + '/runtime/photocraft-gpu/sample.png'], options.backend)
    print(f'PhotoCraft {options.backend} probe: client job={client.pid}, X11={server.pid}', flush=True)
    try:
        code = client.wait(timeout=options.duration)
        print('PhotoCraft exited:', code, flush=True)
    except subprocess.TimeoutExpired:
        print('PhotoCraft remained running throughout the bounded probe', flush=True)
    print((work / (options.backend + '.log')).read_text(errors='replace')[-10000:], flush=True)
finally:
    for process, stamp in reversed(processes):
        if process.poll() is None and identity(process.pid) == stamp and stamp[1] == process.pid:
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if identity(process.pid) == stamp:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait(timeout=3)
