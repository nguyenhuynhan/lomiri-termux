#!/usr/bin/env python3
"""Register the verified PhotoCraft Vulkan/SHM path without restarting Lomiri."""
import hashlib
import json
from pathlib import Path
import shlex

from app_catalog import register

root = Path(__file__).resolve().parent.parent
runtime = root / 'runtime'
image = runtime / 'app-home/Applications/photocraft-0.18.0-linux-aarch64.AppImage'
expected = 'ce3002bb8c5e6b783ac6a2d9c1cd033e08fb9ad5e7d75cd3da4d0c9bedbdc5ff'
if not image.is_file():
    raise SystemExit('The tested PhotoCraft 0.18.0 AppImage is missing.')
with image.open('rb') as source:
    digest = hashlib.file_digest(source, 'sha256').hexdigest()
if digest != expected:
    raise SystemExit('The tested PhotoCraft 0.18.0 AppImage is missing or has changed.')
lib = runtime / 'gpu-experiments/kgsl-root/usr/lib/aarch64-linux-gnu'
if not (lib / 'libvulkan_freedreno.so').is_file():
    raise SystemExit('The private KGSL/Turnip driver is missing; see the GPU report.')

work = runtime / 'photocraft-gpu'
work.mkdir(parents=True, exist_ok=True)
icd = work / 'freedreno.json'
icd.write_text(json.dumps({'file_format_version': '1.0.1', 'ICD': {
    'library_path': str(lib / 'libvulkan_freedreno.so'), 'api_version': '1.4.363'
}}, indent=2) + '\n')
wrapper = image.parent / 'lomiri-photocraft-gpu'
command = ['/usr/bin/env']
for key in ('LIBGL_ALWAYS_SOFTWARE', 'GALLIUM_DRIVER', 'LD_PRELOAD', 'DISPLAY',
            'VK_ICD_FILENAMES', 'MESA_LOADER_DRIVER_OVERRIDE', 'LIBGL_DRIVERS_PATH',
            '__EGL_VENDOR_LIBRARY_FILENAMES', 'PHOTOCRAFT_NEW_INSTANCE'):
    command += ['-u', key]
command += ['WINIT_UNIX_BACKEND=wayland', 'WGPU_BACKEND=vulkan', 'MESA_VK_WSI_DEBUG=sw',
            'LD_LIBRARY_PATH=' + str(lib), 'VK_DRIVER_FILES=' + str(icd),
            'APPIMAGE_EXTRACT_AND_RUN=1', 'PHOTOCRAFT_NO_DESKTOP_INTEGRATION=1',
            str(image)]
wrapper.write_text('#!/bin/sh\nexec ' + shlex.join(command) + ' "$@"\n')
wrapper.chmod(0o700)

desktop = runtime / 'data/applications/ai.storyteller.photocraft.desktop'
desktop.parent.mkdir(parents=True, exist_ok=True)
backup = work / 'original-photocraft.desktop'
if desktop.exists() and not backup.exists():
    backup.write_bytes(desktop.read_bytes())
desktop.write_text(
    '[Desktop Entry]\nType=Application\nName=PhotoCraft (GPU)\n'
    'GenericName=Image Editor\nComment=PhotoCraft with Adreno Vulkan in Lomiri\n'
    f'Exec={shlex.quote(str(wrapper))}\nIcon=ai.storyteller.photocraft\n'
    'Terminal=false\nStartupNotify=false\nStartupWMClass=ai.storyteller.photocraft\n'
    'Categories=Graphics;2DGraphics;RasterGraphics;Photography;\n'
    'X-Lomiri-Touch=true\nX-Lomiri-Single-Instance=true\n')
register('ai.storyteller.photocraft', str(wrapper), {})
print('Registered PhotoCraft (GPU): Vulkan rendering, shared-memory presentation.')
print('Open the Lomiri menu entry or run lomiri-photocraft. No shell restart needed.')
