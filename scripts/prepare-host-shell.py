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
        '        usageScenario: {\n            return lomiriSettings.usageMode === "Windowed" ? "desktop" : (root.width > root.height ? "tablet" : "phone");',
}
for before, after in changes.items():
    if text.count(before) != 1:
        raise RuntimeError(f'Unsupported Lomiri QML revision: {before}')
    text = text.replace(before, after)
before = '        objectName: "shell"'
if text.count(before) != 1:
    raise RuntimeError('Unsupported OrientedShell mode switch revision')
text = text.replace(before, before + '\n        onHostModeToggleRequested: {\n'
    '            lomiriSettings.usageMode = lomiriSettings.usageMode === "Windowed" ? "Staged" : "Windowed";\n'
    '        }')
before = '    function calculateUsageMode() {'
if text.count(before) != 1:
    raise RuntimeError('Unsupported OrientedShell automatic mode revision')
text = text.replace(before, before + '\n        return; // The dock controls this private session mode, including on resize.')
path.write_text(text)
window = target / 'ShellScreen.qml'
text = window.read_text()
before = '    title: "Lomiri Shell"'
if text.count(before) != 1:
    raise RuntimeError('Unsupported Lomiri ShellScreen revision')
text = text.replace('import QtQuick 2.15', 'import QtQuick 2.15\nimport QtQuick.Window 2.2 as HostWindow')
text = text.replace(before, before + '\n    width: HostWindow.Screen.width\n    height: HostWindow.Screen.height')
before = '            implicitWidth: screenWindow.width\n            implicitHeight: screenWindow.height'
if text.count(before) != 1:
    raise RuntimeError('Unsupported ShellScreen viewport binding revision')
text = text.replace(before, before + '\n            width: screenWindow.width\n            height: screenWindow.height')
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

def replace_once(text, before, after):
    if text.count(before) != 1:
        raise RuntimeError(f'Unsupported Lomiri dock QML revision: {before}')
    return text.replace(before, after)


# Keep upstream's app drawer and activation path; replace only the side strip.
shutil.copyfile(root / 'src/HostDock.qml', target / 'HostDock.qml')
shell = target / 'Shell.qml'
text = shell.read_text()
text = replace_once(text, '    id: shell', '    id: shell\n    signal hostModeToggleRequested()')
text = replace_once(text,
    'anchors.leftMargin: (launcher.lockedByUser && launcher.lockAllowed) ? launcher.panelWidth : 0',
    'anchors.leftMargin: 0\n        anchors.bottomMargin: hostDock.height')
text = replace_once(text,
    '        id: stages\n        objectName: "stages"\n        width: parent.width\n        height: parent.height',
    '        id: stages\n        objectName: "stages"\n        width: parent.width\n        height: parent.height - hostDock.height')
text = replace_once(text, 'launcherLeftMargin: launcher.visibleWidth', 'launcherLeftMargin: 0')
text = replace_once(text,
    'leftMargin: (launcher.lockedByUser && launcher.lockAllowed) ? launcher.panelWidth : 0',
    'leftMargin: 0\n            bottomMargin: hostDock.height')
text = replace_once(text, 'applicationMenuContentX: launcher.lockedVisible ? launcher.panelWidth : 0',
    'applicationMenuContentX: 0')
text = replace_once(text, '            minimizedPanelHeight: units.gu(3)',
    '            minimizedPanelHeight: units.gu(shell.usageScenario === "desktop" ? 5.5 : 3)')
text = replace_once(text,
    '            fullscreenMode: (focusedSurfaceIsFullscreen && !LightDMService.greeter.active && launcher.progress == 0 && !stage.spreadShown)\n'
    '                            || greeter.hasLockedApp',
    '            fullscreenMode: shell.usageScenario !== "desktop" &&\n'
    '                ((focusedSurfaceIsFullscreen && !LightDMService.greeter.active && launcher.progress == 0 && !stage.spreadShown) || greeter.hasLockedApp)')
text = replace_once(text,
    '            width: parent.width\n            dragAreaWidth: shell.edgeSize',
    '            width: parent.width\n            dragAreaWidth: 0')
text = replace_once(text, '            available: tutorial.launcherEnabled',
    '            available: false && tutorial.launcherEnabled')
text = replace_once(text, '            lockedVisible: (lockedByUser || shell.atDesktop) && lockAllowed',
    '            lockedVisible: false')
text = replace_once(text,
    '            anchors.topMargin: inverted ? 0 : panel.panelHeight\n            anchors.bottom: parent.bottom',
    '            anchors.topMargin: inverted ? 0 : panel.panelHeight\n'
    '            anchors.bottom: parent.bottom\n            anchors.bottomMargin: hostDock.height')
text = replace_once(text, '        KeyboardShortcutsOverlay {', '''        HostDock {
            id: hostDock
            z: 100
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            desktopMode: shell.usageScenario === "desktop"
            onModeToggleRequested: {
                launcher.hide();
                stage.closeSpread();
                shell.hostModeToggleRequested();
            }
            onOverviewRequested: {
                launcher.hide();
                stage.hostToggleSpread();
            }
            onDrawerRequested: launcher.toggleDrawer(false)
            onApplicationSelected: {
                launcher.hide();
                greeter.notifyUserRequestedApp();
                shell.activateApplication(appId);
            }
        }

        KeyboardShortcutsOverlay {''')
shell.write_text(text)
launcher = target / 'Launcher/Launcher.qml'
text = launcher.read_text()
text = replace_once(text, '        panelWidth: panel.width', '        panelWidth: 0')
text = replace_once(text, '        visible: root.x > 0 || x > -width || dragArea.pressed',
    '        visible: false')
launcher.write_text(text)

# Keep native window actions accessible without a mouse hover, also in F11.
panel = target / 'Panel/Panel.qml'
text = panel.read_text()
text = replace_once(text,
    'property bool showWindowDecorationControls: (revealControls && panelState.decorationsVisible) ||',
    'property bool showWindowDecorationControls: panelState.decorationsVisible ||')
panel.write_text(text)
stage = target / 'Stage/Stage.qml'
text = stage.read_text()
text = replace_once(text, '    function closeSpread() {',
    '    function hostToggleSpread() { priv.goneToSpread = !priv.goneToSpread; }\n\n'
    '    function closeSpread() {')
text = replace_once(text, 'readonly property real windowDecorationHeight: units.gu(3)',
    'readonly property real windowDecorationHeight: units.gu(5.5)')
text = replace_once(text,
    'priv.focusedAppDelegate.maximized && !root.spreadShown',
    '(priv.focusedAppDelegate.maximized || priv.focusedAppDelegate.fullscreen) && !root.spreadShown')
text = replace_once(text,
    'value: priv.focusedAppDelegate && priv.focusedAppDelegate.maximized',
    'value: priv.focusedAppDelegate && (priv.focusedAppDelegate.maximized || priv.focusedAppDelegate.fullscreen)')
text = replace_once(text,
    '                            requestedX: 0\n                            requestedY: 0',
    '                            requestedX: root.availableDesktopArea.x\n'
    '                            requestedY: root.availableDesktopArea.y')
text = replace_once(text,
    '                            requestedWidth: appContainer.width\n                            requestedHeight: appContainer.height',
    '                            requestedWidth: root.availableDesktopArea.width\n'
    '                            requestedHeight: root.availableDesktopArea.height')
stage.write_text(text)

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
