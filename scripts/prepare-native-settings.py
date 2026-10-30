#!/usr/bin/env python3
"""Restore the packaged Lomiri Settings launcher in this private session."""
import os
import json
from pathlib import Path
import shutil

root = Path(__file__).resolve().parent.parent
data = Path(os.environ['XDG_DATA_HOME']).resolve()
if data != (root / 'runtime/data').resolve():
    raise RuntimeError('Native Settings metadata must stay inside the private session')
source = Path('/usr/share/applications/lomiri-system-settings.desktop')
if source.exists():
    destination = data / 'applications/lomiri-system-settings.desktop'
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)

    # PluginManager scans GenericDataLocation in order, keeping the last
    # manifest with each name. The native app alone adds this directory last.
    native = root / 'runtime/native-data/lomiri-system-settings'
    upstream = Path('/usr/share/lomiri-system-settings')
    background = native / 'qml-plugins/background'
    shutil.copytree(upstream / 'qml-plugins/background', background, dirs_exist_ok=True)

    def patch(filename, before, after):
        path = background / filename
        text = path.read_text()
        if text.count(before) != 1:
            raise RuntimeError(f'Unsupported native Settings revision: {filename}: {before}')
        path.write_text(text.replace(before, after))

    patch('MainPage.qml', 'readonly property string welcomeBackground: backgroundPanel.backgroundFile',
          'readonly property string welcomeBackground: shellSettings.backgroundPictureUri')
    patch('utilities.js',
          'backgroundPanel.backgroundFile = backgroundPanel.prepareBackgroundFile(uri, true);',
          'var prepared = backgroundPanel.prepareBackgroundFile(uri, true);\n'
          '    if (prepared) shellSettings.backgroundPictureUri = prepared;')
    patch('utilities.js', 'repeater.itemAt(i).state = "";',
          'var item = repeater.itemAt(i);\n        if (item) item.state = "";')
    patch('utilities.js', 'if (repeater.itemAt(i).state === "selected") {',
          'var item = repeater.itemAt(i);\n        if (item && item.state === "selected") {')
    preview = background / 'Preview.qml'
    text = preview.read_text()
    if text.count('if (headerStyle.hasOwnProperty("textColor"))') != 2:
        raise RuntimeError('Unsupported native Settings Preview revision')
    preview.write_text(text.replace('if (headerStyle.hasOwnProperty("textColor"))',
                                   'if (headerStyle && headerStyle.hasOwnProperty("textColor"))'))
    patch('WallpaperGrid.qml', 'if (gridRepeater.itemAt(i).state === "selected") {',
          'var item = gridRepeater.itemAt(i);\n                if (item && item.state === "selected") {')
    patch('WallpaperGrid.qml', 'height: state === "" ? childrenRect.height : header.height',
          'height: state === "" ? header.height + grid.height + '
          '(isCustom ? addremove.height : units.gu(2)) : header.height')
    manifest = json.loads((upstream / 'background.settings').read_text())
    manifest['page-component'] = (background / 'MainPage.qml').as_uri()
    (native / 'background.settings').write_text(json.dumps(manifest, indent=2) + '\n')

    sound = native / 'qml-plugins/sound'
    shutil.copytree(upstream / 'qml-plugins/sound', sound, dirs_exist_ok=True)
    utility = sound / 'utilities.js'
    text = utility.read_text()
    before = 'return title[0].toUpperCase() + title.slice(1)'
    if text.count(before) != 1:
        raise RuntimeError('Unsupported native Settings sound names revision')
    utility.write_text(text.replace(before, 'return title ? title[0].toUpperCase() + title.slice(1) : ""'))
    sound_page = sound / 'PageComponent.qml'
    text = sound_page.read_text()
    text = text.replace('property bool serverChecked: soundActionGroup.silentMode.state',
                        'enabled: soundActionGroup.silentMode.state !== undefined\n'
                        '                    property bool serverChecked: soundActionGroup.silentMode.state === true')
    text = text.replace('enabled: soundActionGroup.volume.state != null',
                        'enabled: soundActionGroup.volume.state !== undefined && soundActionGroup.volume.state !== null')
    text = text.replace('property real serverValue: soundActionGroup.volume.state',
                        'property real serverValue: soundActionGroup.volume.state || 0')
    sound_page.write_text(text)
    manifest = json.loads((upstream / 'sound.settings').read_text())
    manifest['page-component'] = sound_page.as_uri()
    (native / 'sound.settings').write_text(json.dumps(manifest, indent=2) + '\n')
