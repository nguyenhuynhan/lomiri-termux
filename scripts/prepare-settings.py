#!/usr/bin/env python3
"""Install Settings resources into this session's private data directory."""
import os
from pathlib import Path
import shutil
import subprocess

ROOT = Path(__file__).resolve().parent.parent


def prepare():
    data = Path(os.environ['XDG_DATA_HOME']).resolve()
    if data != (ROOT / 'runtime/data').resolve():
        raise RuntimeError('Settings resources must stay inside the private session')
    schemas = data / 'glib-2.0/schemas'
    schemas.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT / 'src/com.lomiri.Termux.gschema.xml',
                    schemas / 'com.lomiri.Termux.gschema.xml')
    subprocess.run(['glib-compile-schemas', '--strict', str(schemas)], check=True)
    apps = data / 'applications'
    apps.mkdir(parents=True, exist_ok=True)
    # Quote desktop arguments independently; the broker verifies the exact script.
    script = str(ROOT / 'scripts/guest-settings.py')
    quoted = script.replace('\\', '\\\\').replace('"', '\\"').replace('`', '\\`').replace('$', '\\$')
    (apps / 'lomiri-session-settings.desktop').write_text(
        '[Desktop Entry]\nType=Application\nName=Session Settings\nName[vi]=Cài đặt phiên Lomiri\n'
        'Comment=Customize the Lomiri session\n'
        f'Icon={ROOT / "apps/settings.svg"}\n'
        f'Exec=/usr/bin/python3 "{quoted}"\n'
        'Terminal=false\nCategories=Settings;\nX-Lomiri-Touch=true\n'
        'X-Lomiri-Single-Instance=true\n', encoding='utf-8')


if __name__ == '__main__':
    prepare()
