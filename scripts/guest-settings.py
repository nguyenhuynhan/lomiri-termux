#!/usr/bin/env python3
"""Launch the QML Settings client using only the private session configuration."""
import json
import os
from pathlib import Path

root = Path(__file__).resolve().parent.parent
env = os.environ.copy()
env.update(json.loads((root / 'runtime/guest-session-env.json').read_text()))
env['GSETTINGS_SCHEMA_DIR'] = str(root / 'runtime/data/glib-2.0/schemas')
env.update(QT_QPA_PLATFORM='wayland', WAYLAND_DISPLAY='wayland-0',
           QT_SCALE_FACTOR='1', QT_AUTO_SCREEN_SCALE_FACTOR='0', QT_FONT_DPI='96',
           QT_WAYLAND_DISABLE_WINDOWDECORATION='1', QT_SELECT='qt5',
           LIBGL_ALWAYS_SOFTWARE='1', GALLIUM_DRIVER='llvmpipe')
for key in ('DISPLAY', 'LD_PRELOAD', 'LD_LIBRARY_PATH', 'MIR_SOCKET'):
    env.pop(key, None)
env['DESKTOP_FILE_HINT'] = str(root / 'runtime/data/applications/lomiri-session-settings.desktop')
binary = '/usr/lib/qt5/bin/qmlscene'
os.execve(binary, [binary, str(root / 'apps/SessionSettings.qml')], env)
