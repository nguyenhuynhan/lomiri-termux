#!/usr/bin/env python3
"""Catalog refresh and boundary checks, isolated from the live Lomiri session."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch, Mock

root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root / 'scripts'))
import app_catalog as catalog


with tempfile.TemporaryDirectory(prefix='catalog-', dir=root / 'runtime') as folder:
    folder = Path(folder)
    catalog.ROOT = folder
    catalog.CATALOG = folder / 'catalog.json'
    assert catalog.read_catalog() == {}
    catalog.register('test-one', '/usr/bin/true', {})
    assert catalog.read_catalog()['test-one']['executable'] == '/usr/bin/true'
    catalog.register('test-two', '/usr/bin/false', {'WGPU_BACKEND': 'gl'})
    assert set(catalog.read_catalog()) == {'test-one', 'test-two'}
    records = json.loads(catalog.CATALOG.read_text())
    for invalid in [
        {'executable': 'relative', 'environment': {}},
        {'executable': '/tmp/other', 'environment': {}},
        {'executable': '/usr/bin/../tmp/other', 'environment': {}},
        {'executable': '/usr/bin/true', 'environment': {'LD_PRELOAD': '/tmp/injected.so'}},
    ]:
        catalog.CATALOG.write_text(json.dumps({'invalid': invalid}))
        try:
            catalog.read_catalog()
            raise AssertionError('Invalid catalog was accepted')
        except ValueError:
            pass
    catalog.CATALOG.write_text(json.dumps(records))
    images = folder / 'runtime/app-home/Applications'
    desktops = folder / 'runtime/data/applications'
    images.mkdir(parents=True)
    desktops.mkdir(parents=True)
    appimage = images / 'photocraft-0.18.0-linux-aarch64.AppImage'
    appimage.write_bytes(b'isolated discovery fixture')
    desktop = desktops / 'ai.storyteller.photocraft.desktop'
    desktop.write_text(f'[Desktop Entry]\nType=Application\nExec="{appimage}" %F\n')
    assert catalog.read_catalog()['ai.storyteller.photocraft']['executable'] == str(appimage)
    desktop.write_text('[Desktop Entry]\nExec=/bin/sh -c "unapproved command"\n')
    assert 'ai.storyteller.photocraft' not in catalog.read_catalog()
    desktop.write_text(f'[Desktop Entry]\nExec="{appimage}" %F\n')
    appimage.unlink()
    assert 'ai.storyteller.photocraft' not in catalog.read_catalog()
    spec = importlib.util.spec_from_file_location('app_services_under_test', root / 'scripts/guest-app-services.py')
    service = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(service)
    service.RUNTIME = folder
    owner = {'pid': 1}
    manager = SimpleNamespace(owner=owner, units={}, active=lambda: owner,
                              new_job=lambda name: name, UnitNew=Mock())
    binary = '/usr/bin/true'
    def launch(app, executable=binary, args=None):
        return service.AppServices.StartTransientUnit(
            manager, f'lomiri-app-launch--test--{app}--.service', 'replace',
            [('Environment', [f'APP_ID={app}']),
             ('ExecStart', [(executable, args or [executable], False)])], [])
    process = Mock(pid=123)
    process.poll.return_value = None
    with patch.object(service.subprocess, 'Popen', return_value=process) as spawn, \
         patch.object(service, 'AppUnit', return_value=SimpleNamespace(path='/test', process=process)):
        try:
            launch('new-without-restart')
            raise AssertionError('Unregistered application accepted')
        except service.Rejected:
            pass
        catalog.register('new-without-restart', binary, {'WGPU_BACKEND': 'gl'})
        launch('new-without-restart')
        assert spawn.call_count == 1
        assert spawn.call_args.kwargs['env']['WGPU_BACKEND'] == 'gl'
        for app, executable, args in [('test-one', '/usr/bin/false', None),
                                      ('test-two', '/usr/bin/false', ['/usr/bin/false', 'extra'])]:
            try:
                launch(app, executable, args)
                raise AssertionError('Executable/argument mismatch accepted')
            except service.Rejected:
                pass
        assert spawn.call_count == 1
        catalog.CATALOG.write_text('{invalid json')
        launch('lomiri-calculator-app', '/usr/bin/lomiri-calculator-app')
        assert spawn.call_count == 2, 'A broken extra catalog must not block existing apps'
print('PASS: new app detected in the same process; invalid paths/environment rejected; installed app discovery refreshed')
print('PASS: same app-service instance accepts a newly registered app; executable/argument checks retained; existing apps tolerate an invalid extra catalog')
