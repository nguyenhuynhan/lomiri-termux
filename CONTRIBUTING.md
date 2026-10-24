# Contributing

Reproduction reports and focused fixes are welcome. Preserve Android and existing Termux, Ubuntu, XFCE, coding, and AI profiles. Do not use broad process-kill commands or alter bootloader/SELinux settings.

## Report a problem

Include phone architecture, Android/Termux:X11 versions, guest package versions, launch mode, and exact steps. Distinguish visible UI, application launch, input, rotation, and battery measurements. Share only relevant, redacted log excerpts. Keep runtime profiles, credentials, pairing codes, and private files out of issues and commits.

## Validate a change

In Termux, from the project directory:

```bash
mkdir -p runtime
for script in scripts/*.sh; do bash -n "$script"; done
python tests/session-lifecycle.py
bash scripts/build-input-compat.sh
```

The build runs a real Qt window delivery test before recording package versions and the library hash. Without the bridge, that test must reproduce missing mouse delivery. Input/graphics changes also need an actual Lomiri session; offscreen tests alone do not prove device usability.

For lifecycle changes, confirm that stop/start affects only this experiment and an unrelated display still responds. Report exact versions and remaining limitations in the pull request.

## Useful next steps

- Reliable keyboard resize and portrait/landscape adaptation.
- Native application launch without missing systemd services.
- Gestures, scrolling, and IME composition.
- Scoped GPU and battery measurements.
- A suitable upstream fix to replace the private Qt ABI bridge.

Original contributions use the repository's MIT license. Installed upstream packages retain their own licenses.
