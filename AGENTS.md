# Project rules

- This project runs a real Lomiri shell in a Linux container inside the existing Termux environment.
- The working PoC uses lomiri-debian (Debian trixie, Mir 2.20). The initial mobile-ubuntu attempt crashed in QtMir's older rendering path; preserve that evidence.
- Preserve Android, mobile-ubuntu, existing XFCE/Code/AI setup and user projects.
- Keep experimental settings and logs inside this project. Do not change the user's default desktop.
- Distinguish package installation, renderer probes, visible shell, application launch, input/rotation and battery measurements.
- Default to direct Lomiri on its own tagged Termux:X11 display (:2), as requested by the user. Retain nested mode as a development option. Use software rendering until GPU evidence supports changing it.
- Stop only the process group created by this project; verify PID identity before sending signals.
- Never use broad killall/pkill for the user's other apps. Do not automatically unlock the bootloader or change SELinux.
- Record failures and exact runtime versions in docs/progress.md. Keep raw logs and screenshots out of Git.
- Do not create a commit, push or publish unless the user asks.
