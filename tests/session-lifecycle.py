#!/usr/bin/env python3
"""Exercise ownership guards with disposable processes, never the user's apps."""
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time
import unittest

SOURCE = Path(__file__).resolve().parent.parent


class SessionLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="lifecycle-", dir=SOURCE / "runtime")
        self.root = Path(self.tmp.name).resolve()
        (self.root / "scripts").mkdir()
        (self.root / "runtime").mkdir()
        self.manager = self.root / "scripts" / "session-state.py"
        shutil.copyfile(SOURCE / "scripts" / "session-state.py", self.manager)
        self.children = []

    def run_manager(self, action):
        return subprocess.run([sys.executable, str(self.manager), action], capture_output=True, text=True)

    def start_fixture(self, name="session.sh"):
        script = self.root / "scripts" / name
        script.write_text(f'"{sys.executable}" "{self.manager}" register\nsleep 30 &\nwait\n')
        child = subprocess.Popen([shutil.which("bash"), str(script)], start_new_session=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.children.append(child)
        for _ in range(30):
            if (self.root / "runtime" / "session.json").exists():
                return child
            time.sleep(0.1)
        self.fail("Fixture did not register")

    def tearDown(self):
        for child in self.children:
            try:
                os.killpg(child.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            child.wait(timeout=5)
        self.tmp.cleanup()

    def test_owned_session_stops(self):
        child = self.start_fixture()
        self.assertEqual(self.run_manager("status").returncode, 0)
        result = self.run_manager("stop")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        child.wait(timeout=5)

    def test_stale_start_time_is_not_signalled(self):
        child = self.start_fixture()
        state = self.root / "runtime" / "session.json"
        data = json.loads(state.read_text())
        data["start_time"] = "0"
        state.write_text(json.dumps(data))
        self.assertEqual(self.run_manager("stop").returncode, 0)
        self.assertIsNone(child.poll())

    def test_other_command_is_not_signalled(self):
        child = self.start_fixture("other-app.sh")
        self.assertEqual(self.run_manager("stop").returncode, 0)
        self.assertIsNone(child.poll())


if __name__ == "__main__":
    unittest.main(verbosity=2)
