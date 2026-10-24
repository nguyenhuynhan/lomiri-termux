#!/usr/bin/env python3
"""Add diagnostics to a private copy of installed Lomiri QML, leaving packages intact."""
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent.parent
target = root / 'runtime' / 'lomiri-qml'
shutil.copytree('/usr/share/lomiri', target, dirs_exist_ok=True)
shell = target / 'Shell.qml'
text = shell.read_text()
marker = '    id: shell\n'
if marker not in text:
    raise RuntimeError('Installed Shell.qml does not match the expected diagnostic insertion point')
probe = '''    Timer {
        interval: 1000
        repeat: true
        running: true
        property int samples: 0
        onTriggered: {
            console.log("POC_STAGE", "state=" + stage.state,
                        "interactive=" + stage.interactive,
                        "allowed=" + stage.allowInteractivity,
                        "greeter=" + (greeter ? greeter.shown : "none"),
                        "panelClosed=" + panel.indicators.fullyClosed,
                        "modal=" + notifications.useModal,
                        "launcherFocus=" + launcher.takesFocus);
            if (++samples >= 30) stop();
        }
    }
'''
shell.write_text(text.replace(marker, marker + probe, 1))
print('Private diagnostic QML entry:', target / 'ShellApplication.qml')
