#!/usr/bin/env bash
source "$(dirname -- "$0")/common.sh"
guest_root /usr/bin/env DEBIAN_FRONTEND=noninteractive /bin/bash -c '
set -e
apt-get update
apt-get install -y --no-install-recommends python3-dbus python3-gi \
  lomiri-app-launch-tools lomiri-content-hub pulseaudio-utils libqt5multimedia5-plugins \
  lomiri-terminal-app lomiri-filemanager-app lomiri-calculator-app lomiri-clock-app \
  lomiri-calendar-app lomiri-gallery-app lomiri-mediaplayer-app
'
echo 'Core applications installed. Restart Lomiri to load its private app services.'
