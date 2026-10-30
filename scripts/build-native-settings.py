#!/usr/bin/env python3
"""Rebuild the native 1.3.1 frontend with upstream's search-anchor null guards.

Keep installed native libraries/plugins; write only project runtime files.
Source SHA256 is from Debian's lomiri-system-settings_1.3.1-6.dsc.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import tarfile
import urllib.request

root = Path(__file__).resolve().parent.parent
work = root / 'runtime/native-build'
work.mkdir(parents=True, exist_ok=True)
archive = work / 'lomiri-system-settings_1.3.1.orig.tar.bz2'
checksum = 'cca7ea7bee4202b3ab6f29d601efadfdf40f2500165542a778c8e40ddfc461e5'
if not archive.exists():
    url = 'https://deb.debian.org/debian/pool/main/l/lomiri-system-settings/' + archive.name
    with urllib.request.urlopen(url, timeout=60) as response:
        archive.write_bytes(response.read())
if hashlib.sha256(archive.read_bytes()).hexdigest() != checksum:
    raise RuntimeError('Native Settings source archive checksum mismatch')
with tarfile.open(archive) as source_archive:
    source_archive.extractall(work, filter='data')
source = work / 'lomiri-system-settings-1.3.1'
window = source / 'src/qml/MainWindow.qml'
text = window.read_text()
before = 'left: parent.left\n                        right: parent.right\n                        verticalCenter: parent.verticalCenter'
after = 'left: parent ? parent.left : undefined\n                        right: parent ? parent.right : undefined\n                        verticalCenter: parent ? parent.verticalCenter : undefined'
if text.count(before) != 1:
    raise RuntimeError('Unsupported native search field anchors')
text = text.replace(before, after)
window.write_text(text)

# Build the existing frontend sources against the matching packaged ABI.
# No reimplementation of PluginManager, QML entry point or native backends.
driver = work / 'frontend'
driver.mkdir(exist_ok=True)
driver.joinpath('CMakeLists.txt').write_text('''cmake_minimum_required(VERSION 3.16)
project(native_settings_frontend LANGUAGES CXX)
set(CMAKE_AUTOMOC ON)
set(CMAKE_CXX_STANDARD 17)
find_package(Qt5 REQUIRED COMPONENTS Core Gui Quick Qml DBus Widgets)
find_package(PkgConfig REQUIRED)
pkg_check_modules(GLIB REQUIRED IMPORTED_TARGET glib-2.0)
get_filename_component(SOURCE "${CMAKE_CURRENT_SOURCE_DIR}/../lomiri-system-settings-1.3.1" ABSOLUTE)
qt5_add_resources(RESOURCES "${SOURCE}/src/ui.qrc")
add_executable(lomiri-system-settings
  "${SOURCE}/src/debug.cpp" "${SOURCE}/src/item-model.cpp"
  "${SOURCE}/src/main.cpp" "${SOURCE}/src/plugin-manager.cpp"
  "${SOURCE}/src/plugin.cpp" "${SOURCE}/src/utils.cpp" ${RESOURCES})
target_include_directories(lomiri-system-settings PRIVATE "${SOURCE}/src" "${SOURCE}/lib"
  "${SOURCE}/lib/LomiriSystemSettingsPrivate")
target_compile_definitions(lomiri-system-settings PRIVATE
  I18N_DIRECTORY="/usr/share/locale" I18N_DOMAIN="lomiri-system-settings"
  MANIFEST_DIR="lomiri-system-settings" QML_DIR="qml-plugins"
  PLUGIN_MANIFEST_DIR="/usr/share/lomiri-system-settings"
  PLUGIN_MODULE_DIR="/usr/lib/aarch64-linux-gnu/lomiri-system-settings"
  PLUGIN_PRIVATE_MODULE_DIR="/usr/lib/aarch64-linux-gnu/lomiri-system-settings/private"
  PLUGIN_QML_DIR="/usr/share/lomiri-system-settings/qml-plugins")
target_link_libraries(lomiri-system-settings Qt5::Core Qt5::Gui Qt5::Quick Qt5::Qml
  Qt5::DBus Qt5::Widgets PkgConfig::GLIB
  /lib/aarch64-linux-gnu/libLomiriSystemSettings.so.1
  /lib/aarch64-linux-gnu/libLomiriSystemSettingsPrivate.so.0.0)
''')
build = work / 'build'
subprocess.run(['cmake', '-S', str(driver), '-B', str(build), '-DCMAKE_BUILD_TYPE=Release'], check=True)
subprocess.run(['cmake', '--build', str(build), '--parallel', '2'], check=True)
binary = build / 'lomiri-system-settings'
work.joinpath('build.json').write_text(json.dumps({
    'source_version': '1.3.1', 'source_sha256': checksum,
    'packaged_binary_sha256': hashlib.sha256(Path('/usr/bin/lomiri-system-settings').read_bytes()).hexdigest(),
    'binary_sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
    'fix': 'Null parent guards for search field anchors, matching upstream MainWindow.qml',
}, indent=2) + '\n')
print('Native Settings frontend built:', binary)
