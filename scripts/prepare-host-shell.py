#!/usr/bin/env python3
"""Build a private QML overlay: Android owns rotation; Lomiri follows viewport."""
import hashlib
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent.parent
source = Path('/usr/share/lomiri')
target = root / 'runtime/host-qml'
shutil.copytree(source, target, dirs_exist_ok=True)
path = target / 'OrientedShell.qml'
text = path.read_text()
changes = {
    'property int acceptedOrientationAngle: {':
        'property int acceptedOrientationAngle: {\n        return 0; // Android already rotated the X11 viewport.',
    'property int physicalOrientation: QtQuickWindow.Screen.orientation':
        'property int physicalOrientation: root.width > root.height ? Qt.LandscapeOrientation : Qt.PortraitOrientation',
    '        usageScenario: {':
        '        usageScenario: {\n            return root.width > root.height ? "tablet" : "phone";',
}
for before, after in changes.items():
    if text.count(before) != 1:
        raise RuntimeError(f'Unsupported Lomiri QML revision: {before}')
    text = text.replace(before, after)
path.write_text(text)
window = target / 'ShellScreen.qml'
text = window.read_text()
before = '    title: "Lomiri Shell"'
if text.count(before) != 1:
    raise RuntimeError('Unsupported Lomiri ShellScreen revision')
text = text.replace('import QtQuick 2.15', 'import QtQuick 2.15\nimport QtQuick.Window 2.2 as HostWindow')
text = text.replace(before, before + '\n    width: HostWindow.Screen.width\n    height: HostWindow.Screen.height')
window.write_text(text)
greeter = target / 'Greeter/ShimGreeter.qml'
text = greeter.read_text()
if 'function notifyAppFocusRequested(' not in text:
    before = '    // Since ShimGreeter is never active, these can just return'
    if text.count(before) != 1:
        raise RuntimeError('Unsupported ShimGreeter revision')
    text = text.replace(before, '    function notifyAppFocusRequested(appId) {}\n\n' + before)
greeter.write_text(text)

application = target / 'ShellApplication.qml'
text = application.read_text()
before = '    id: root'
if text.count(before) != 1:
    raise RuntimeError('Unsupported ShellApplication revision')
text = text.replace(before, before + '\n    property Timer hostReadyTimer: Timer {\n'
                    '        interval: 500; running: true; repeat: false\n'
                    '        onTriggered: console.log("LOMIRI_SHELL_READY")\n    }')
application.write_text(text)

pulse = Path(__import__('os').environ['XDG_CONFIG_HOME']) / 'pulse/client.conf'
pulse.parent.mkdir(parents=True, exist_ok=True)
if not pulse.exists():
    pulse.write_text('enable-shm = no\nenable-memfd = no\n')
(root / 'runtime/host-shell.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256((source / path.name).read_bytes()).hexdigest(),
    'overlay_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    'rotation': 'Android viewport; no second rotation in Lomiri',
}, indent=2))

applications = Path(__import__('os').environ['XDG_DATA_HOME']) / 'applications'
applications.mkdir(parents=True, exist_ok=True)
for name, title, binary, icon in [
    ('lomiri-code', 'Visual Studio Code', '/usr/share/code/code', '/usr/share/pixmaps/vscode.png'),
    ('lomiri-chatgpt', 'ChatGPT (Firefox)', '/usr/bin/firefox-esr', '/usr/share/icons/hicolor/128x128/apps/firefox-esr.png'),
]:
    (applications / f'{name}.desktop').write_text(
        f'[Desktop Entry]\nType=Application\nName={title}\nExec={binary}\nIcon={icon}\n'
        'Terminal=false\nX-Lomiri-Touch=true\nX-Lomiri-Single-Instance=true\n')
for name in ('com.microsoft.VSCode', 'com.microsoft.VSCode.UrlHandler', 'firefox-esr',
             'miral-shell', 'lomiri-probe', 'lomiri-system-settings'):
    (applications / f'{name}.desktop').write_text(
        '[Desktop Entry]\nType=Application\nName=Unavailable in PRoot\nHidden=true\n')

settings = root / 'runtime/vscode/user-data/User/settings.json'
settings.parent.mkdir(parents=True, exist_ok=True)
values = json.loads(settings.read_text()) if settings.exists() else {}
for key, value in {'files.simpleDialog.enable': True, 'terminal.integrated.gpuAcceleration': 'off',
                   'python.defaultInterpreterPath': '/usr/bin/python3'}.items():
    values.setdefault(key, value)
settings.write_text(json.dumps(values, indent=2))
