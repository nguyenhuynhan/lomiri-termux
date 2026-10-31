#!/usr/bin/env python3
"""Add ArtCraft to this Lomiri session's private catalog."""
from pathlib import Path
from app_catalog import register

root = Path(__file__).resolve().parent.parent
applications = root / 'runtime/data/applications'
applications.mkdir(parents=True, exist_ok=True)
desktop = applications / 'ai.storyteller.artcraft-launcher.desktop'
desktop.write_text(
    '[Desktop Entry]\nType=Application\nName=ArtCraft Launcher\n'
    'Comment=Install, update and open the Craft apps\n'
    'Exec=/usr/bin/artcraft-launcher\nIcon=ai.storyteller.artcraft-launcher\n'
    'Terminal=false\nCategories=Graphics;\n'
    'X-Lomiri-Touch=true\nX-Lomiri-Single-Instance=true\n')
register('ai.storyteller.artcraft-launcher', '/usr/bin/artcraft-launcher',
         {'WGPU_BACKEND': 'gl', 'WINIT_UNIX_BACKEND': 'wayland', 'APPIMAGE_EXTRACT_AND_RUN': '1'})
