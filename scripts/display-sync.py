#!/usr/bin/env python3
"""Keep the sole Mir host window aligned with the owned direct X display.

Android changes the X root size when its viewport or keyboard changes. Listen
for X events instead of polling, and never resize a display with multiple host
windows or one not owned by this project session.
"""
import ctypes as c
import ctypes.util
import os
from pathlib import Path
import runpy
import sys

root = Path(__file__).resolve().parent.parent
manager = runpy.run_path(str(root / 'scripts/session-state.py'))
owner = manager['active']()
if owner.get('mode') != 'direct' or os.getpgrp() != owner['pid']:
    sys.exit('Display sync must run inside the owned direct session.')
x = c.CDLL(ctypes.util.find_library('X11') or 'libX11.so')
Window = c.c_ulong
x.XOpenDisplay.argtypes = [c.c_char_p]
x.XOpenDisplay.restype = c.c_void_p
x.XDefaultRootWindow.argtypes = [c.c_void_p]
x.XDefaultRootWindow.restype = Window
x.XQueryTree.argtypes = [c.c_void_p, Window, c.POINTER(Window), c.POINTER(Window),
                         c.POINTER(c.POINTER(Window)), c.POINTER(c.c_uint)]
x.XGetGeometry.argtypes = [c.c_void_p, Window, c.POINTER(Window), c.POINTER(c.c_int),
    c.POINTER(c.c_int), c.POINTER(c.c_uint), c.POINTER(c.c_uint), c.POINTER(c.c_uint), c.POINTER(c.c_uint)]
x.XSelectInput.argtypes = [c.c_void_p, Window, c.c_long]
x.XMoveResizeWindow.argtypes = [c.c_void_p, Window, c.c_int, c.c_int, c.c_uint, c.c_uint]
x.XMapRaised.argtypes = [c.c_void_p, Window]
x.XNextEvent.argtypes = [c.c_void_p, c.c_void_p]
x.XFlush.argtypes = [c.c_void_p]
x.XFree.argtypes = [c.c_void_p]
display = x.XOpenDisplay(sys.argv[1].encode())
if not display:
    sys.exit('Owned X display is unavailable.')
xroot = x.XDefaultRootWindow(display)
# StructureNotify on the root, plus creation/configuration of its direct children.
x.XSelectInput(display, xroot, (1 << 17) | (1 << 19))
last = None


def geometry(window):
    parent = Window()
    px, py = c.c_int(), c.c_int()
    width, height, border, depth = c.c_uint(), c.c_uint(), c.c_uint(), c.c_uint()
    if not x.XGetGeometry(display, window, c.byref(parent), c.byref(px), c.byref(py),
                         c.byref(width), c.byref(height), c.byref(border), c.byref(depth)):
        raise RuntimeError('Host window disappeared.')
    return width.value, height.value


while True:
    current = manager['active']()
    if current != owner:
        sys.exit('Session ownership changed; display sync stopped.')
    children = c.POINTER(Window)()
    count = c.c_uint()
    tree_root, parent = Window(), Window()
    x.XQueryTree(display, xroot, c.byref(tree_root), c.byref(parent), c.byref(children), c.byref(count))
    if count.value == 1:
        window = children[0]
        size = geometry(xroot)
        if last != (window, size) or geometry(window) != size:
            x.XMoveResizeWindow(display, window, 0, 0, *size)
            x.XMapRaised(display, window)
            x.XFlush(display)
            last = window, size
            print(f'Synced Mir host window: {size[0]}x{size[1]}', flush=True)
    x.XFree(children)
    event = (c.c_long * 24)()
    x.XNextEvent(display, c.byref(event))
