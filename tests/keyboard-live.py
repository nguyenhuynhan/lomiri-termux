#!/usr/bin/env python3
"""Launch a synthetic Qt input probe using QtMir's supported desktop hint."""
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
env = os.environ.copy()
env.update(json.loads((ROOT / 'runtime/guest-session-env.json').read_text()))
env.pop('LD_PRELOAD', None)
env.update(QT_QPA_PLATFORM='wayland', WAYLAND_DISPLAY='wayland-0', QT_SELECT='qt5',
           LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe', QT_SCALE_FACTOR='1',
           QT_AUTO_SCREEN_SCALE_FACTOR='0', QT_WAYLAND_DISABLE_WINDOWDECORATION='1', QT_FONT_DPI='96')
desktop = ROOT / 'runtime/data/applications/lomiri-keyboard-probe.desktop'
desktop.write_text('[Desktop Entry]\nType=Application\nName=Thử bàn phím\nNoDisplay=true\n'
                   'Icon=applications-development\nTerminal=false\nX-Lomiri-Touch=true\n'
                   f'Exec=/usr/lib/qt5/bin/qmlscene {ROOT}/tests/KeyboardProbe.qml\n')
env['DESKTOP_FILE_HINT'] = str(desktop)
binary = '/usr/lib/qt5/bin/qmlscene'
os.execve(binary, [binary, str(ROOT / 'tests/KeyboardProbe.qml')], env)
