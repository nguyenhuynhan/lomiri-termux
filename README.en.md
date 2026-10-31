# Lomiri on Termux

Run the **real Lomiri shell** on Android using Termux:X11 and a separate Debian PRoot environment. The default launcher opens Lomiri directly in its own Android window without starting XFCE.

[Tiếng Việt](README.md)

This is an early proof of concept tested on a OnePlus 13, ARM64. The device owner has confirmed basic tapping and typing in a real Qt/Wayland application. It is not a complete Ubuntu Touch installation or a reliable daily desktop yet.

## Architecture

```text
Android -> Termux:X11 :2 -> Mir X11 backend -> QtMir/Lomiri -> Wayland clients
```

Android retains control of the device. This project does not unlock the bootloader, replace Android, or require Android root. Debian `lomiri-debian` is separate from any existing Ubuntu/XFCE workstation.

## Install

Start with official [Termux](https://github.com/termux/termux-app), the shared-UID [Termux:X11](https://github.com/termux/termux-x11) app/companion package, and [PRoot-Distro](https://github.com/termux/proot-distro). Termux needs `git`, `python`, `xdotool`, `xorg-xrandr`, and `util-linux` as well. Allow enough disk space for Debian, desktop packages, and compiler headers. Other phones require device validation.

In Termux:

```bash
git clone https://github.com/nguyenhuynhan/lomiri-termux.git ~/projects/lomiri-termux
cd ~/projects/lomiri-termux
bash scripts/install-debian.sh
bash scripts/install-demo-deps.sh
bash scripts/build-input-compat.sh --install-deps
bash scripts/install-shortcuts.sh
lomiri-start
```

Packages come from the selected guest's official repositories. Debian packages are not mixed into an existing Ubuntu guest. The default guest user is `dev`.

`lomiri-start` creates a private tagged X display on `:2`; repeated calls bring the same Android window forward. The canonical activity URI is `termux-x11-window://lomiri-poc`. Mixing it with a bare URI can create duplicate Android tasks.

For Android shortcuts, open Termux:Widget and choose **Create shortcuts** and **Refresh widgets**. Long-press its launcher icon for **Lomiri** and **Stop Lomiri**.

```bash
# Real Qt/Wayland application to test input:
bash ~/projects/lomiri-termux/scripts/demo-app.sh
lomiri-status
# Save your work before stopping:
lomiri-stop
```

Stopping validates PID, start time, process group, and command identity before signalling only this experiment's group. An existing XFCE display `:1` stays available. No wake lock or Android boot startup is added. Locking Android is not Linux hibernation; Android may terminate background processes.

## Work applications

Microsoft VSCode ARM64 1.143.1 and Firefox ESR 153.5.1 have been device-tested as Wayland clients. The editor saved a Python file and its integrated terminal ran it. ChatGPT web accepted `2+2` and answered `4` without signing in.

```bash
bash scripts/install-work-apps.sh
bash scripts/install-shortcuts.sh
lomiri-stop
lomiri-code --no-sandbox
lomiri-chatgpt
```

The tested PRoot setup needed VSCode's `--no-sandbox`, reducing Electron's sandbox. This remains opt-in by default; the tested phone enables `LOMIRI_CODE_NO_SANDBOX=1` privately. Firefox keeps its default sandbox configuration. App profiles, extension data and the scratch workspace stay in `runtime/`; existing credentials are not imported.

Review the scratch folder before accepting Workspace Trust. The local broker starts only these two apps in the owned session process group; stopping the recorded application/session processes was device-tested. It accepts no arbitrary shell command.

Launch with `lomiri-code`, `lomiri-chatgpt` or the corresponding Widget shortcuts. Use Alt+Tab to switch and Lomiri's titlebar square to maximize. Sign in to your account manually when needed; see the [official web quickstart](https://learn.chatgpt.com/docs/web).

To keep the display awake, choose **Screen idle timeout → Never (keep screen on)** in Termux:X11 preferences and leave X11 in front. It uses more battery. Restore **System**, leave X11 or lock the phone to let it rest.

## Android keyboard and Vietnamese

The tested phone now uses **Unexpected Keyboard 2.1.0 in English with
Fcitx5/UniKey Telex in Debian**. Run `bash scripts/install-keyboard.sh` for the
Linux integration, select Unexpected in Android, save work and restart Lomiri.
Session Settings controls automatic keyboard opening and Vietnamese; the dock's
VN/EN button switches composition. Android uses Ctrl+Space to switch system IMEs.

ADB tests covered automatic opening, Vietnamese composition and repeated
Backspace in Qt, Terminal, VSCode, ChatGPT Desktop and Firefox. The shell's
drawer/search supports English and may need manual keyboard opening.
The device owner confirmed automatic opening, correct Vietnamese composition
and five successive Backspaces in the keyboard probe. Rotation with the keyboard
open and prolonged/fast typing remain unconfirmed.
See the [keyboard report](docs/keyboard-20261031.md).

## Local Qt input bridge

The tested QtMir package posts mouse events to a plain `QtEventFeeder` QObject. A local preload library routes only that receiver's mouse events to the shell QWindow through Qt5's input interface. It preserves fractional coordinates, buttons, and modifiers; other receivers retain their original dispatch path.

System Qt libraries are not replaced. The bridge uses a private ABI; package versions and its hash are checked at startup. Rebuild with `bash scripts/build-input-compat.sh` after Qt/QtMir upgrades, then stop/start Lomiri. Normal sessions do not load diagnostic QML, the input probe, or the crash handler.

## Evidence and limitations

The tested stack is Debian trixie ARM64, Lomiri 0.5.0-2, Mir 2.20.2-2, QtMir 0.8.0~git20250407.ea2f477-1+deb13u1, Qt 5.15.15, and Mesa llvmpipe 25.0.7. Safe stop/restart and idempotent start were tested on the phone. A real Qt window test reproduces missing mouse delivery without the bridge and passes with it.

An event-driven bridge follows the owned X display's viewport, with Xvfb tests for resize, unrelated windows and stale ownership. A duplicate Android task with the same tag was removed during device verification. Full rotation/layout behavior, gestures, scrolling, fast Vietnamese typing, GPU performance, battery use and long-term stability still require work. Fast injected input sometimes lost characters; slower pacing completed the desktop-app tests. Software rendering remains the baseline. The older Ubuntu stack's rendering crash remains documented.

Runtime logs, profiles, configuration, and built libraries stay in ignored `runtime/` or `config.env`. Read the [architecture](docs/architecture.md), [experiment log in Vietnamese](docs/progress.md), and [contribution guide](CONTRIBUTING.md).

Original project code is [MIT licensed](LICENSE). Installed Lomiri, Mir, QtMir, Qt, Termux, and application packages retain their upstream licenses; their binaries are not distributed here.

Upstream: [Lomiri](https://gitlab.com/ubports/development/core/lomiri), [QtMir](https://gitlab.com/ubports/development/core/qtmir), [tested feeder source](https://gitlab.com/ubports/development/core/qtmir/-/blob/ea2f477/src/platforms/mirserver/qteventfeeder.cpp), [Debian package](https://packages.debian.org/trixie/lomiri).

## ArtCraft and PhotoCraft GPU

Install the ARM64 ArtCraft Launcher into the private Debian guest with
`bash scripts/install-artcraft.sh`, then use the Lomiri menu or `lomiri-artcraft`.
The adapter reads an explicit catalog for each launch and detects installed
Craft AppImages without restarting the shell.

With the tested private Turnip/KGSL driver already prepared, run
`bash scripts/install-photocraft-gpu.sh` and open PhotoCraft from the Lomiri
menu or `lomiri-photocraft`. PhotoCraft 0.18.0 uses Adreno Vulkan rendering
and Wayland shared-memory presentation inside the existing software shell.
ArtCraft's own Open button still inherits its CPU settings. The phone test
covered opening a PNG, painting and 200% zoom; large documents, battery and
long-term stability remain unverified. See the
[ArtCraft](docs/artcraft-20261031.md) and
[PhotoCraft GPU](docs/photocraft-gpu-20261031.md) reports.
