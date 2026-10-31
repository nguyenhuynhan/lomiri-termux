#!/usr/bin/env python3
"""Translate owned Linux focus events into tagged Android keyboard toggles."""
import ctypes as c
import ctypes.util
import json
import os
from pathlib import Path
import runpy
import selectors
import signal
import socket
import struct
import subprocess
import sys
import time

from keyboard_policy import KeyboardPolicy

ROOT = Path(__file__).resolve().parent.parent


class XIEventMask(c.Structure):
    _fields_ = [('deviceid', c.c_int), ('mask_len', c.c_int), ('mask', c.POINTER(c.c_ubyte))]


class XEventCookie(c.Structure):
    _fields_ = [('type', c.c_int), ('serial', c.c_ulong), ('send_event', c.c_int),
                ('display', c.c_void_p), ('extension', c.c_int), ('evtype', c.c_int),
                ('cookie', c.c_uint), ('data', c.c_void_p)]


def main():
    manager = runpy.run_path(str(ROOT / 'scripts/session-state.py'))
    owner = manager['active']()
    if owner.get('mode') != 'direct' or os.getpgrp() != owner['pid']:
        raise RuntimeError('Keyboard host must belong to the owned direct session')
    preferences = subprocess.check_output(['termux-x11-preference', 'list'], text=True, timeout=5)
    if '"backButtonAction"="toggle soft keyboard"' not in preferences:
        raise RuntimeError('Automatic keyboard needs the existing Back action to toggle the keyboard')
    x = c.CDLL(ctypes.util.find_library('X11') or 'libX11.so')
    pointer, window = c.c_void_p, c.c_ulong
    x.XOpenDisplay.argtypes = [c.c_char_p]
    x.XOpenDisplay.restype = pointer
    x.XDefaultRootWindow.argtypes = [pointer]
    x.XDefaultRootWindow.restype = window
    x.XConnectionNumber.argtypes = [pointer]
    x.XConnectionNumber.restype = c.c_int
    x.XGetGeometry.argtypes = [pointer, window, c.POINTER(window), c.POINTER(c.c_int),
        c.POINTER(c.c_int), c.POINTER(c.c_uint), c.POINTER(c.c_uint), c.POINTER(c.c_uint), c.POINTER(c.c_uint)]
    x.XSelectInput.argtypes = [pointer, window, c.c_long]
    x.XPending.argtypes = [pointer]
    x.XNextEvent.argtypes = [pointer, pointer]
    x.XCloseDisplay.argtypes = [pointer]
    x.XQueryExtension.argtypes = [pointer, c.c_char_p, c.POINTER(c.c_int),
                                  c.POINTER(c.c_int), c.POINTER(c.c_int)]
    x.XGetEventData.argtypes = [pointer, c.POINTER(XEventCookie)]
    x.XFreeEventData.argtypes = [pointer, c.POINTER(XEventCookie)]
    x.XFlush.argtypes = [pointer]
    display = x.XOpenDisplay(sys.argv[1].encode())
    if not display:
        raise RuntimeError('Owned X display is unavailable')
    xroot = x.XDefaultRootWindow(display)
    x.XSelectInput(display, xroot, 1 << 17)
    xi = c.CDLL(ctypes.util.find_library('Xi') or 'libXi.so')
    xi.XISelectEvents.argtypes = [pointer, window, c.POINTER(XIEventMask), c.c_int]
    opcode, first_event, first_error = c.c_int(), c.c_int(), c.c_int()
    if not x.XQueryExtension(display, b'XInputExtension', c.byref(opcode),
                            c.byref(first_event), c.byref(first_error)):
        raise RuntimeError('Owned display lacks XInput2 button notifications')
    button_mask = (c.c_ubyte * 2)(0, 1 << 7)  # XI_RawButtonPress only; never observe keys.
    mask = XIEventMask(1, 2, button_mask)  # XIAllMasterDevices on this private X display.
    if xi.XISelectEvents(display, xroot, c.byref(mask), 1):
        raise RuntimeError('Cannot observe input taps on the owned display')
    x.XFlush(display)

    def size():
        parent, px, py = window(), c.c_int(), c.c_int()
        width, height, border, depth = (c.c_uint() for _ in range(4))
        if not x.XGetGeometry(display, xroot, c.byref(parent), c.byref(px), c.byref(py),
                              c.byref(width), c.byref(height), c.byref(border), c.byref(depth)):
            raise RuntimeError('Owned viewport disappeared')
        return width.value, height.value

    policy = KeyboardPolicy(size())
    endpoint = ROOT / 'runtime/keyboard.sock'
    endpoint.unlink(missing_ok=True)
    server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    server.bind(str(endpoint))
    endpoint.chmod(0o600)
    inode = endpoint.stat().st_ino
    selector = selectors.DefaultSelector()
    selector.register(server, selectors.EVENT_READ, 'focus')
    selector.register(x.XConnectionNumber(display), selectors.EVENT_READ, 'viewport')
    running = True
    deadline = None
    tap_deadline = None
    last_sequence = 0
    sender_pid = None

    def stop(_signum, _frame):
        nonlocal running
        running = False

    def toggle(desired):
        nonlocal deadline
        if desired is None:
            return
        if manager['active']() != owner:
            raise RuntimeError('Session ownership changed')
        result = subprocess.run(['am', 'broadcast', '-a', 'com.termux.x11.ACTION_CUSTOM',
                                 '-p', 'com.termux.x11', '--es', 'document_tag', 'lomiri-poc',
                                 '--es', 'what', 'backButton'], capture_output=True, timeout=5)
        if result.returncode:
            policy.failed()
            print('Android keyboard request failed.', flush=True)
        else:
            deadline = time.monotonic() + 2
            print('Keyboard requested:', 'show' if desired else 'hide', flush=True)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while running:
            if manager['active']() != owner:
                break
            deadlines = [value for value in (deadline, tap_deadline) if value is not None]
            timeout = max(0, min(deadlines) - time.monotonic()) if deadlines else 2
            for key, _mask in selector.select(min(timeout, 2)):
                if key.data == 'viewport':
                    while x.XPending(display):
                        event = (c.c_long * 24)()
                        x.XNextEvent(display, c.byref(event))
                        cookie = c.cast(c.byref(event), c.POINTER(XEventCookie))
                        if cookie.contents.type == 35 and cookie.contents.extension == opcode.value:
                            if x.XGetEventData(display, cookie):
                                if cookie.contents.evtype == 15 and policy.focused and not policy.visible:
                                    tap_deadline = time.monotonic() + .25
                                x.XFreeEventData(display, cookie)
                    pending = policy.pending
                    policy.viewport(size())
                    if pending is not None and policy.pending is None:
                        deadline = None
                        toggle(policy.reconcile())
                else:
                    payload, ancillary, flags, _address = server.recvmsg(2048, socket.CMSG_SPACE(12))
                    credentials = next((struct.unpack('3i', data) for level, kind, data in ancillary
                                        if level == socket.SOL_SOCKET and kind == socket.SCM_CREDENTIALS), None)
                    try:
                        message = json.loads(payload)
                        pid = credentials[0] if credentials else 0
                        if (flags & socket.MSG_TRUNC or pid != message['pid']
                                or message['owner_pid'] != owner['pid'] or os.getpgid(pid) != owner['pid']
                                or type(message['focused']) is not bool or type(message['auto']) is not bool):
                            continue
                        if sender_pid != pid:
                            sender_pid, last_sequence = pid, 0
                        if message['sequence'] <= last_sequence:
                            continue
                        last_sequence = message['sequence']
                        toggle(policy.request(message['focused'], message['auto'],
                                              message.get('show_request') is True))
                    except (OSError, ValueError, KeyError, TypeError):
                        continue
            if deadline is not None and time.monotonic() >= deadline:
                policy.failed()
                deadline = None
                print('Keyboard visibility was not confirmed by the viewport.', flush=True)
            if tap_deadline is not None and time.monotonic() >= tap_deadline:
                tap_deadline = None
                toggle(policy.request(policy.focused, force=True))
    finally:
        selector.close()
        server.close()
        x.XCloseDisplay(display)
        if endpoint.exists() and endpoint.stat().st_ino == inode:
            endpoint.unlink()


if __name__ == '__main__':
    main()
