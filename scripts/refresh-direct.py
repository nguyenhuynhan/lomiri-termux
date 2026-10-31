#!/usr/bin/env python3
"""Request a repaint of this session's Mir window after Android restores X11."""
import ctypes as c
import ctypes.util
from pathlib import Path
import runpy

root = Path(__file__).resolve().parent.parent
state = runpy.run_path(str(root / 'scripts/session-state.py'))['active']()
if state.get('mode') != 'direct':
    raise SystemExit(0)
x = c.CDLL(ctypes.util.find_library('X11') or 'libX11.so')
Window = c.c_ulong
x.XOpenDisplay.argtypes = [c.c_char_p]
x.XOpenDisplay.restype = c.c_void_p
x.XDefaultRootWindow.argtypes = [c.c_void_p]
x.XDefaultRootWindow.restype = Window
x.XQueryTree.argtypes = [c.c_void_p, Window, c.POINTER(Window), c.POINTER(Window),
                        c.POINTER(c.POINTER(Window)), c.POINTER(c.c_uint)]
x.XFetchName.argtypes = [c.c_void_p, Window, c.POINTER(c.c_char_p)]
x.XClearArea.argtypes = [c.c_void_p, Window, c.c_int, c.c_int, c.c_uint, c.c_uint, c.c_int]
x.XFlush.argtypes = [c.c_void_p]
x.XFree.argtypes = [c.c_void_p]
x.XCloseDisplay.argtypes = [c.c_void_p]
display = x.XOpenDisplay(b':2')
if not display:
    raise SystemExit(0)
children = c.POINTER(Window)()
count = c.c_uint()
tree_root, parent = Window(), Window()
try:
    x.XQueryTree(display, x.XDefaultRootWindow(display), c.byref(tree_root),
                 c.byref(parent), c.byref(children), c.byref(count))
    if count.value == 1:
        name = c.c_char_p()
        x.XFetchName(display, children[0], c.byref(name))
        try:
            if name.value == b'Lomiri Termux PoC':
                x.XClearArea(display, children[0], 0, 0, 0, 0, 1)
                x.XFlush(display)
        finally:
            if name:
                x.XFree(name)
finally:
    if children:
        x.XFree(children)
    x.XCloseDisplay(display)
