"""Read a small, explicit application catalog on every launch request."""
import json
import os
from pathlib import Path
import re
import configparser
import shlex

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / 'runtime/app-catalog.json'
SAFE_ENV = {
    'WGPU_BACKEND': {'gl', 'vulkan'},
    'WINIT_UNIX_BACKEND': {'wayland'},
    'APPIMAGE_EXTRACT_AND_RUN': {'1'},
}
CRAFT_APPS = ('photocraft', 'lightcraft', 'filmcraft', 'designcraft', 'vectorcraft',
              'pdfcraft', 'effectcraft', 'wordcraft', 'deckcraft', 'gridcraft',
              'cadcraft', 'soundcraft', 'figcraft')
CRAFT_ENV = {'WGPU_BACKEND': 'gl', 'WINIT_UNIX_BACKEND': 'wayland', 'APPIMAGE_EXTRACT_AND_RUN': '1'}


def installed_craft_apps():
    records = {}
    for name in CRAFT_APPS:
        app = 'ai.storyteller.' + name
        paths = [ROOT / 'runtime/data/applications' / f'{app}.desktop',
                 Path('/usr/share/applications') / f'{app}.desktop']
        for desktop in paths:
            if not desktop.is_file() or desktop.is_symlink() or desktop.stat().st_size > 32768:
                continue
            parser = configparser.ConfigParser(interpolation=None)
            try:
                parser.read_string(desktop.read_text())
                args = shlex.split(parser['Desktop Entry']['Exec'])
                if not args or len(args) > 2 or (len(args) == 2 and args[1] not in ('%F', '%f', '%U', '%u')):
                    continue
                binary = Path(args[0])
                if not binary.is_absolute() or not binary.is_file():
                    continue
                appimages = ROOT / 'runtime/app-home/Applications'
                official_package = binary == Path('/usr/bin') / name
                official_image = (binary.parent == appimages and binary.resolve().is_relative_to(appimages.resolve())
                                  and re.fullmatch(re.escape(name) + r'-[0-9][A-Za-z0-9.+-]*-linux-aarch64\.AppImage', binary.name))
                if official_package or official_image:
                    records[app] = {'executable': str(binary), 'environment': CRAFT_ENV.copy()}
                    break
            except (OSError, ValueError, KeyError, configparser.Error):
                continue
    return records


def read_catalog(path=None, discover=True):
    path = CATALOG if path is None else path
    if not path.exists():
        return installed_craft_apps() if discover else {}
    if path.is_symlink() or path.stat().st_size > 65536:
        raise ValueError('Invalid application catalog file')
    records = json.loads(path.read_text())
    if not isinstance(records, dict):
        raise ValueError('Application catalog must be an object')
    for app, record in records.items():
        if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._-]{0,127}', app):
            raise ValueError('Invalid application id')
        if not isinstance(record, dict) or set(record) != {'executable', 'environment'}:
            raise ValueError('Invalid application record')
        binary = Path(record['executable'])
        if not binary.is_absolute() or '..' in binary.parts:
            raise ValueError('Application executable must be an absolute path')
        allowed = (Path('/usr/bin'), Path('/usr/local/bin'), ROOT / 'runtime/app-home/Applications')
        if not any(binary.is_relative_to(folder) for folder in allowed):
            raise ValueError('Application executable is outside approved folders')
        environment = record['environment']
        if not isinstance(environment, dict) or any(
            key not in SAFE_ENV or value not in SAFE_ENV[key] for key, value in environment.items()
        ):
            raise ValueError('Unsupported application environment option')
    return {**installed_craft_apps(), **records} if discover else records


def register(app, executable, environment):
    records = read_catalog(discover=False)
    records[app] = {'executable': executable, 'environment': environment}
    CATALOG.parent.mkdir(parents=True, exist_ok=True)
    temporary = CATALOG.with_suffix('.tmp')
    temporary.write_text(json.dumps(records, indent=2) + '\n')
    temporary.chmod(0o600)
    try:
        read_catalog(temporary, discover=False)
        os.replace(temporary, CATALOG)
    finally:
        temporary.unlink(missing_ok=True)
