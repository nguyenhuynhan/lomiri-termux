#!/usr/bin/env python3
"""Launch two allowed Wayland apps as children of the owned Lomiri session."""
import json
import os
from pathlib import Path
import runpy
import shutil
import signal
import socket
import subprocess

root = Path(__file__).resolve().parent.parent
runtime = root / 'runtime'
state = json.loads((runtime / 'session.json').read_text())
if os.getpgrp() != state['pid']:
    raise RuntimeError('App launcher must belong to the private Lomiri process group.')
identity = runpy.run_path(str(root / 'scripts/session-state.py'))['identity']
endpoint = runtime / 'work-apps.sock'
children = {}


def launch(app, no_sandbox):
    previous = children.get(app)
    if previous and previous[0].poll() is None:
        return {'ok': True, 'message': f'{app} is already running; select its window in Lomiri.'}
    env = os.environ.copy()
    env.update(json.loads((runtime / 'guest-session-env.json').read_text()))
    sockets = sorted(p for p in Path(env['XDG_RUNTIME_DIR']).glob('wayland-*') if p.is_socket())
    if not sockets:
        raise RuntimeError('Lomiri Wayland socket is not ready.')
    for key in ('DISPLAY', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'ELECTRON_RUN_AS_NODE', 'VSCODE_IPC_HOOK_CLI'):
        env.pop(key, None)
    env.update(PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
               WAYLAND_DISPLAY=sockets[0].name, LIBGL_ALWAYS_SOFTWARE='1',
               GALLIUM_DRIVER='llvmpipe', GDK_BACKEND='wayland', MOZ_ENABLE_WAYLAND='1')
    private_home = runtime / 'app-home'
    private_home.mkdir(mode=0o700, parents=True, exist_ok=True)
    env['HOME'] = str(private_home)
    if app == 'code':
        binary = Path('/usr/share/code/code')
        data = runtime / 'vscode/user-data'
        settings = data / 'User/settings.json'
        settings.parent.mkdir(parents=True, exist_ok=True)
        if not settings.exists():
            settings.write_text(json.dumps({'telemetry.telemetryLevel': 'off',
                'workbench.startupEditor': 'none', 'editor.fontSize': 16,
                'terminal.integrated.fontSize': 16, 'window.titleBarStyle': 'custom',
                'window.newWindowDimensions': 'maximized'}))
        workspace = runtime / 'code-workspace'
        workspace.mkdir(parents=True, exist_ok=True)
        example = workspace / 'hello.py'
        if not example.exists():
            shutil.copyfile(root / 'apps/hello-phone.py', example)
        args = [str(binary), '--ozone-platform=wayland', '--disable-gpu',
                '--disable-dev-shm-usage', '--new-window', f'--user-data-dir={data}',
                f'--extensions-dir={runtime / "vscode/extensions"}', str(workspace), str(example)]
        if no_sandbox:
            args.insert(1, '--no-sandbox')
        title, icon = 'VSCode in Lomiri', 'code'
    else:
        binary = Path('/usr/bin/firefox-esr')
        profile = runtime / 'firefox-chatgpt'
        profile.mkdir(mode=0o700, parents=True, exist_ok=True)
        args = [str(binary), '--no-remote', '--profile', str(profile), 'https://chatgpt.com/']
        title, icon = 'ChatGPT in Lomiri', 'firefox-esr'
    if not binary.is_file():
        raise RuntimeError(f'Missing {binary}. Install the work applications first.')
    desktop = Path(env['XDG_DATA_HOME']) / 'applications' / f'lomiri-{app}.desktop'
    desktop.parent.mkdir(parents=True, exist_ok=True)
    desktop.write_text(f'[Desktop Entry]\nType=Application\nName={title}\nIcon={icon}\n'
                       f'Exec={binary}\nTerminal=false\n')
    env['DESKTOP_FILE_HINT'] = str(desktop)
    with (runtime / f'{app}.log').open('a') as log:
        process = subprocess.Popen(args, env=env, cwd=root, stdin=subprocess.DEVNULL,
                                   stdout=log, stderr=subprocess.STDOUT)
    children[app] = process, identity(process.pid)
    records = {name: {'pid': item[0].pid, 'pgid': os.getpgid(item[0].pid),
                     'start_time': item[1]} for name, item in children.items() if item[0].poll() is None}
    (runtime / 'work-apps.json').write_text(json.dumps(records, indent=2))
    return {'ok': True, 'message': f'{app} started (pid={process.pid}). Confirm the visible window.'}


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
            except (OSError, ValueError, RuntimeError) as error:
                result = {'ok': False, 'message': str(error)}
            client.sendall(json.dumps(result).encode())
finally:
    server.close()
    if endpoint.exists() and endpoint.stat().st_ino == inode:
        endpoint.unlink()
    for process, start_time in children.values():
        try:
            if process.poll() is None and identity(process.pid) == start_time:
                process.terminate()
        except OSError:
            pass
