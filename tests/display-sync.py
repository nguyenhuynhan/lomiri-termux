#!/usr/bin/env python3
"""Exercise viewport changes and ownership guards against a disposable Xvfb."""
import ctypes as c
import ctypes.util
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


class DisplaySync(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='display-sync-', dir=SOURCE / 'runtime')
        self.root = Path(self.temp.name)
        (self.root / 'scripts').mkdir()
        (self.root / 'runtime').mkdir()
        for name in ('session-state.py', 'display-sync.py'):
            shutil.copyfile(SOURCE / 'scripts' / name, self.root / 'scripts' / name)
        script = self.root / 'scripts/session.sh'
        script.write_text(f'export LOMIRI_DIRECT=1\n"{sys.executable}" "{self.root}/scripts/session-state.py" register\n'
                          f'Xvfb :89 -screen 0 800x600x24 -nolisten tcp &\n'
                          f'for n in $(seq 1 40); do DISPLAY=:89 xrandr --current >/dev/null 2>&1 && break; sleep .1; done\n'
                          f'"{sys.executable}" "{self.root}/scripts/display-sync.py" :89 > "{self.root}/runtime/sync.log" 2>&1 &\nwait\n')
        self.supervisor = subprocess.Popen(['bash', str(script)], start_new_session=True,
                                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.x = c.CDLL(ctypes.util.find_library('X11'))
        self.x.XOpenDisplay.argtypes = [c.c_char_p]
        self.x.XOpenDisplay.restype = c.c_void_p
        self.x.XDefaultRootWindow.argtypes = [c.c_void_p]
        self.x.XDefaultRootWindow.restype = c.c_ulong
        self.x.XCreateSimpleWindow.argtypes = [c.c_void_p, c.c_ulong, c.c_int, c.c_int, c.c_uint, c.c_uint, c.c_uint, c.c_ulong, c.c_ulong]
        self.x.XCreateSimpleWindow.restype = c.c_ulong
        self.x.XGetGeometry.argtypes = [c.c_void_p, c.c_ulong, c.POINTER(c.c_ulong), c.POINTER(c.c_int), c.POINTER(c.c_int),
            c.POINTER(c.c_uint), c.POINTER(c.c_uint), c.POINTER(c.c_uint), c.POINTER(c.c_uint)]
        self.x.XMapWindow.argtypes = [c.c_void_p, c.c_ulong]
        self.x.XDestroyWindow.argtypes = [c.c_void_p, c.c_ulong]
        self.x.XFlush.argtypes = [c.c_void_p]
        self.display = None
        for _ in range(40):
            self.display = self.x.XOpenDisplay(b':89')
            if self.display: break
            time.sleep(.1)
        self.assertTrue(self.display, 'Disposable X server did not start')
        self.xroot = self.x.XDefaultRootWindow(self.display)

    def tearDown(self):
        try:
            os.killpg(self.supervisor.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        self.supervisor.wait(timeout=5)
        self.temp.cleanup()

    def window(self, width, height):
        result = self.x.XCreateSimpleWindow(self.display, self.xroot, 0, 0, width, height, 0, 0, 0)
        self.x.XMapWindow(self.display, result)
        self.x.XFlush(self.display)
        return result

    def size(self, window):
        root = c.c_ulong()
        px, py = c.c_int(), c.c_int()
        width, height, border, depth = c.c_uint(), c.c_uint(), c.c_uint(), c.c_uint()
        self.x.XGetGeometry(self.display, window, c.byref(root), c.byref(px), c.byref(py),
            c.byref(width), c.byref(height), c.byref(border), c.byref(depth))
        return width.value, height.value

    def expect_size(self, window, expected):
        for _ in range(40):
            if self.size(window) == expected: return
            time.sleep(.1)
        self.fail(f'Expected {expected}, got {self.size(window)}; {(self.root / "runtime/sync.log").read_text()}')

    def resize_root(self, width, height):
        env = dict(os.environ, DISPLAY=':89')
        subprocess.run(['xrandr', '--output', 'screen', '--off', '--fb', f'{width}x{height}'], env=env, check=True,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_resize_refuses_other_windows_and_stale_ownership(self):
        primary = self.window(100, 90)
        self.expect_size(primary, (800, 600))
        self.resize_root(640, 480)
        self.expect_size(primary, (640, 480))
        other = self.window(42, 43)
        self.resize_root(500, 400)
        time.sleep(.3)
        self.assertEqual(self.size(primary), (640, 480))
        self.assertEqual(self.size(other), (42, 43))
        self.x.XDestroyWindow(self.display, other)
        self.x.XFlush(self.display)
        self.expect_size(primary, (500, 400))
        state_path = self.root / 'runtime/session.json'
        state = json.loads(state_path.read_text())
        state['start_time'] = '0'
        state_path.write_text(json.dumps(state))
        self.resize_root(400, 300)
        time.sleep(.3)
        self.assertEqual(self.size(primary), (500, 400))


if __name__ == '__main__':
    unittest.main(verbosity=2)
