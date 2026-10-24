#!/usr/bin/env python3
"""Track and stop only this project's process group, including PID reuse checks."""
import json
import os
from pathlib import Path
import signal
import sys
import time

ROOT = Path(__file__).resolve().parent.parent
STATE = ROOT / "runtime" / "session.json"


def identity(pid):
    # /proc comm can contain spaces and parentheses; field 22 follows the last ') '.
    stat = Path(f"/proc/{pid}/stat").read_text().rsplit(") ", 1)[1].split()
    if stat[0] == "Z":
        raise ProcessLookupError("Session process has exited")
    return stat[19]


def active():
    data = json.loads(STATE.read_text())
    pid = data["pid"]
    if data["project"] != str(ROOT) or identity(pid) != data["start_time"]:
        raise ProcessLookupError("Stale session identity")
    if os.getpgid(pid) != pid:
        raise ProcessLookupError("Process group does not belong to this session")
    cmdline = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")
    expected = ROOT / "scripts" / "session.sh"
    matches = any(Path(os.fsdecode(arg)).resolve() == expected for arg in cmdline if arg.endswith(b"/session.sh"))
    if not matches:
        raise ProcessLookupError("Command does not belong to this project")
    return data


def main():
    command = sys.argv[1]
    if command == "register":
        pid = os.getppid()
        if os.getpgid(pid) != pid:
            raise RuntimeError("Use scripts/start.sh to create a private process group")
        STATE.parent.mkdir(exist_ok=True)
        tmp = STATE.with_suffix(".tmp")
        tmp.write_text(json.dumps({"pid": pid, "start_time": identity(pid), "project": str(ROOT),
                                   "mode": "direct" if os.environ.get("LOMIRI_DIRECT") == "1" else "nested"}))
        tmp.replace(STATE)
        return 0
    try:
        data = active()
    except (OSError, ValueError, KeyError, ProcessLookupError):
        print("Lomiri session is not running (or its state is stale).")
        return 1 if command == "status" else 0
    if command == "status":
        print(f"Lomiri session running: pid={data['pid']}")
        return 0
    if command == "stop":
        os.killpg(data["pid"], signal.SIGTERM)
        for _ in range(50):
            time.sleep(0.1)
            try:
                active()
            except (OSError, ValueError, KeyError, ProcessLookupError):
                # Preserve a newer session if another launch happened during shutdown.
                try:
                    if json.loads(STATE.read_text()) == data:
                        STATE.unlink(missing_ok=True)
                except (OSError, ValueError):
                    pass
                print("Lomiri session stopped. Existing desktop remains open.")
                return 0
        print("Session has not exited yet; inspect runtime/session.log. No forced kill performed.")
        return 2
    raise ValueError(f"Unknown command: {command}")


if __name__ == "__main__":
    sys.exit(main())
