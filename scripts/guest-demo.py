#!/usr/bin/env python3
import json
import os
from pathlib import Path
import shutil
import sys

root = Path(__file__).resolve().parent.parent
env = os.environ.copy()
env.update(json.loads((root / 'runtime' / 'guest-session-env.json').read_text()))
sockets = sorted(p for p in Path(env['XDG_RUNTIME_DIR']).glob('wayland-*') if p.is_socket())
if not sockets:
    sys.exit('No active Lomiri Wayland socket. Inspect runtime/session.log.')
qmlscene = '/usr/lib/qt5/bin/qmlscene'
if not Path(qmlscene).exists():
    qmlscene = shutil.which('qmlscene')
if not qmlscene:
    sys.exit('Missing qmlscene. Install the qmlscene package inside the selected guest first.')
env.update(QT_QPA_PLATFORM='wayland', WAYLAND_DISPLAY=sockets[0].name,
           QT_SELECT='qt5', LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe',
           QT_SCALE_FACTOR='1', QT_AUTO_SCREEN_SCALE_FACTOR='0',
           QT_WAYLAND_DISABLE_WINDOWDECORATION='1', QT_FONT_DPI='96')
desktop = Path(env['XDG_DATA_HOME']) / 'applications' / 'lomiri-probe.desktop'
desktop.parent.mkdir(parents=True, exist_ok=True)
desktop.write_text('[Desktop Entry]\nType=Application\nName=Hello Lomiri\n'
                   'Icon=applications-development\n'
                   f'Exec={qmlscene} {root}/apps/HelloLomiri.qml\n'
                   'Terminal=false\nX-Ubuntu-Touch=true\n')
# QtMir documents this hint for manually launched, non-app-launch-managed clients.
env['DESKTOP_FILE_HINT'] = str(desktop)
if os.environ.get('LOMIRI_INPUT_TRACE') == '1':
    env['WAYLAND_DEBUG'] = 'client'
os.execve(qmlscene, [qmlscene, str(root / 'apps' / 'HelloLomiri.qml')], env)
