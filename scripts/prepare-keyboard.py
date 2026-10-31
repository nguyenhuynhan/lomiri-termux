#!/usr/bin/env python3
"""Create an isolated Fcitx profile without replacing existing preferences."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def prepare():
    config = Path(os.environ['XDG_CONFIG_HOME']).resolve()
    if config != (ROOT / 'runtime/config').resolve():
        raise RuntimeError('Keyboard configuration must stay in the Lomiri project')
    folder = config / 'fcitx5'
    folder.mkdir(parents=True, exist_ok=True)
    defaults = {
        'profile': '[Groups/0]\nName=Default\nDefault Layout=us\nDefaultIM=unikey\n\n'
                   '[Groups/0/Items/0]\nName=keyboard-us\nLayout=\n\n'
                   '[Groups/0/Items/1]\nName=unikey\nLayout=\n\n[GroupOrder]\n0=Default\n',
        'config': '[Behavior]\nShareInputState=All\nPreeditEnabledByDefault=True\n',
    }
    for name, text in defaults.items():
        target = folder / name
        if not target.exists():
            target.write_text(text, encoding='utf-8')
            target.chmod(0o600)
    data = Path(os.environ['XDG_DATA_HOME']).resolve()
    if data != (ROOT / 'runtime/data').resolve():
        raise RuntimeError('Keyboard addon metadata must stay in the Lomiri project')
    addons = data / 'fcitx5/addon'
    addons.mkdir(parents=True, exist_ok=True)
    (addons / 'lomirikeyboardfocus.conf').write_text(
        '[Addon]\nName=Lomiri keyboard focus\nType=SharedLibrary\n'
        'Library=liblomirikeyboardfocus\nCategory=Module\nVersion=1\n'
        '[Addon/Dependencies]\n0=core:5.1.12\n')
    applications = data / 'applications'
    applications.mkdir(parents=True, exist_ok=True)
    for name in ('org.fcitx.Fcitx5.desktop', 'fcitx5-wayland-launcher.desktop',
                 'fcitx5-configtool.desktop', 'org.fcitx.fcitx5-config-qt.desktop',
                 'org.fcitx.fcitx5-migrator.desktop', 'org.fcitx.fcitx5-qt5-gui-wrapper.desktop',
                 'kbd-layout-viewer5.desktop'):
        (applications / name).write_text('[Desktop Entry]\nType=Application\nName=Input method service\nHidden=true\n')


if __name__ == '__main__':
    prepare()
