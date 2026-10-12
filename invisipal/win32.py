"""Thin ctypes wrappers around the Win32 APIs Invisipal relies on.

Everything platform-specific lives here so the rest of the code stays readable
(and so the pure-Python modules can be unit-tested on any OS).
"""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    user32 = ctypes.WinDLL("user32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
else:  # pragma: no cover - lets tests import this module elsewhere
    user32 = kernel32 = None

# --- Display affinity -------------------------------------------------------
WDA_NONE = 0x00
WDA_MONITOR = 0x01  # pre-2004 fallback: window shows up as a black box
WDA_EXCLUDEFROMCAPTURE = 0x11  # Windows 10 2004+: window is simply not captured

# --- Window styles ----------------------------------------------------------
GWL_EXSTYLE = -20
WS_EX_TRANSPARENT = 0x00000020
WS_EX_TOOLWINDOW = 0x00000080
WS_EX_APPWINDOW = 0x00040000
WS_EX_LAYERED = 0x00080000

SWP_NOSIZE = 0x0001
SWP_NOMOVE = 0x0002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_FRAMECHANGED = 0x0020
GA_ROOT = 2

# --- Hotkeys / messages -----------------------------------------------------
MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000

WM_QUIT = 0x0012
WM_HOTKEY = 0x0312
PM_NOREMOVE = 0x0000
PM_REMOVE = 0x0001
QS_ALLINPUT = 0x04FF
WAIT_OBJECT_0 = 0x00000000
INFINITE = 0xFFFFFFFF
ERROR_ALREADY_EXISTS = 183

MONITOR_DEFAULTTONULL = 0

VK_SHIFT = 0x10
VK_CONTROL = 0x11
VK_MENU = 0x12
VK_LCONTROL = 0xA2
VK_RMENU = 0xA5

if IS_WINDOWS:
    _LONG_PTR = ctypes.c_ssize_t
    if hasattr(user32, "GetWindowLongPtrW"):
        _get_long = user32.GetWindowLongPtrW
        _set_long = user32.SetWindowLongPtrW
    else:  # 32-bit Python
        _get_long = user32.GetWindowLongW
        _set_long = user32.SetWindowLongW
    _get_long.argtypes = [wintypes.HWND, ctypes.c_int]
    _get_long.restype = _LONG_PTR
    _set_long.argtypes = [wintypes.HWND, ctypes.c_int, _LONG_PTR]
    _set_long.restype = _LONG_PTR

    user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    user32.GetAncestor.restype = wintypes.HWND
    user32.SetWindowDisplayAffinity.argtypes = [wintypes.HWND, wintypes.DWORD]
    user32.SetWindowDisplayAffinity.restype = wintypes.BOOL
    user32.GetWindowDisplayAffinity.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowDisplayAffinity.restype = wintypes.BOOL
    user32.SetWindowPos.argtypes = [
        wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
        ctypes.c_int, ctypes.c_int, wintypes.UINT,
    ]
    user32.SetWindowPos.restype = wintypes.BOOL
    user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
    user32.GetForegroundWindow.restype = wintypes.HWND
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.IsWindow.argtypes = [wintypes.HWND]
    user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
    user32.RegisterHotKey.restype = wintypes.BOOL
    user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
    user32.PeekMessageW.argtypes = [
        ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT, wintypes.UINT,
    ]
    user32.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.MsgWaitForMultipleObjects.argtypes = [
        wintypes.DWORD, ctypes.POINTER(wintypes.HANDLE), wintypes.BOOL, wintypes.DWORD, wintypes.DWORD,
    ]
    user32.MsgWaitForMultipleObjects.restype = wintypes.DWORD
    user32.MonitorFromRect.argtypes = [ctypes.POINTER(wintypes.RECT), wintypes.DWORD]
    user32.MonitorFromRect.restype = wintypes.HMONITOR
    user32.GetKeyboardLayout.argtypes = [wintypes.DWORD]
    user32.GetKeyboardLayout.restype = wintypes.HKL
    user32.MapVirtualKeyExW.argtypes = [wintypes.UINT, wintypes.UINT, wintypes.HKL]
    user32.MapVirtualKeyExW.restype = wintypes.UINT
    user32.ToUnicodeEx.argtypes = [
        wintypes.UINT, wintypes.UINT, ctypes.POINTER(ctypes.c_ubyte),
        wintypes.LPWSTR, ctypes.c_int, wintypes.UINT, wintypes.HKL,
    ]
    user32.ToUnicodeEx.restype = ctypes.c_int
    kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
    kernel32.CreateEventW.restype = wintypes.HANDLE
    kernel32.SetEvent.argtypes = [wintypes.HANDLE]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel32.GetCurrentThreadId.restype = wintypes.DWORD


# --- Process setup ----------------------------------------------------------

def enable_dpi_awareness() -> None:
    """Render crisp text on high-DPI screens (must run before Tk starts)."""
    if not IS_WINDOWS:
        return
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # system DPI aware
    except (AttributeError, OSError):
        try:
            user32.SetProcessDPIAware()
        except (AttributeError, OSError):
            pass


def claim_single_instance(name: str = "Local\\Invisipal.SingleInstance.v1"):
    """Return an event handle if we are the first instance, else ``None``.

    The named event doubles as a "please show yourself" signal: a second
    launch sets it and exits, and the running instance wakes up and appears.
    """
    if not IS_WINDOWS:
        return 0
    ctypes.set_last_error(0)
    handle = kernel32.CreateEventW(None, False, False, name)
    if handle and ctypes.get_last_error() == ERROR_ALREADY_EXISTS:
        kernel32.SetEvent(handle)
        kernel32.CloseHandle(handle)
        return None
    return handle


# --- Window helpers ---------------------------------------------------------

def toplevel_hwnd(tk_widget_id: int) -> int:
    """Tk's ``winfo_id()`` is an inner child window; return the real top-level."""
    return user32.GetAncestor(tk_widget_id, GA_ROOT) or tk_widget_id


def set_capture_excluded(hwnd: int, excluded: bool = True) -> str:
    """Hide (or un-hide) a window from screen capture / screen sharing.

    Returns ``"excluded"`` (invisible to capture), ``"blackout"`` (older Windows,
    shown as a black rectangle), ``"off"`` (deliberately visible) or ``"failed"``.
    """
    if not excluded:
        return "off" if user32.SetWindowDisplayAffinity(hwnd, WDA_NONE) else "failed"
    if user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE):
        return "excluded"
    if user32.SetWindowDisplayAffinity(hwnd, WDA_MONITOR):
        return "blackout"
    return "failed"


def get_display_affinity(hwnd: int) -> int | None:
    value = wintypes.DWORD()
    if user32.GetWindowDisplayAffinity(hwnd, ctypes.byref(value)):
        return value.value
    return None


def affinity_status(hwnd: int, wanted: bool) -> str:
    """Translate the window's current affinity into the same vocabulary as above."""
    value = get_display_affinity(hwnd)
    if value == WDA_EXCLUDEFROMCAPTURE:
        return "excluded"
    if value == WDA_MONITOR:
        return "blackout"
    if value == WDA_NONE:
        return "failed" if wanted else "off"
    return "failed"


def update_ex_style(hwnd: int, add: int = 0, remove: int = 0) -> None:
    style = _get_long(hwnd, GWL_EXSTYLE)
    new_style = (style | add) & ~remove
    if new_style != style:
        _set_long(hwnd, GWL_EXSTYLE, new_style)
        user32.SetWindowPos(
            hwnd, None, 0, 0, 0, 0,
            SWP_NOMOVE | SWP_NOSIZE | SWP_NOZORDER | SWP_NOACTIVATE | SWP_FRAMECHANGED,
        )


def set_click_through(hwnd: int, enabled: bool) -> None:
    """Let mouse clicks fall through the window to whatever is behind it."""
    if enabled:
        update_ex_style(hwnd, add=WS_EX_LAYERED | WS_EX_TRANSPARENT)
    else:
        update_ex_style(hwnd, remove=WS_EX_TRANSPARENT)


def set_taskbar_visible(hwnd: int, visible: bool) -> None:
    """Tool windows have no taskbar button and are skipped by Alt+Tab."""
    if visible:
        update_ex_style(hwnd, add=WS_EX_APPWINDOW, remove=WS_EX_TOOLWINDOW)
    else:
        update_ex_style(hwnd, add=WS_EX_TOOLWINDOW, remove=WS_EX_APPWINDOW)


def window_rect(hwnd: int) -> tuple[int, int, int, int]:
    """(x, y, width, height) of a window in physical screen pixels."""
    rect = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(rect))
    return rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top


def foreground_window() -> int:
    return user32.GetForegroundWindow() or 0


def restore_foreground(hwnd: int) -> None:
    if hwnd and user32.IsWindow(hwnd):
        user32.SetForegroundWindow(hwnd)


def rect_is_on_screen(x: int, y: int, width: int, height: int) -> bool:
    """True if the title-bar area of the rectangle lands on some monitor."""
    if not IS_WINDOWS:
        return True
    rect = wintypes.RECT(x + 20, y, x + max(width - 20, 40), y + 40)
    return bool(user32.MonitorFromRect(ctypes.byref(rect), MONITOR_DEFAULTTONULL))


def ctrl_alt_produces_char(vk: int) -> str | None:
    """Return the character AltGr+key types on the active layout, if any.

    On many layouts AltGr is reported as Ctrl+Alt, so a global Ctrl+Alt+Q
    hotkey would swallow "@" on Latin American / German keyboards.
    """
    if not IS_WINDOWS:
        return None
    hkl = user32.GetKeyboardLayout(0)
    state = (ctypes.c_ubyte * 256)()
    for key in (VK_CONTROL, VK_MENU, VK_LCONTROL, VK_RMENU):
        state[key] = 0x80
    scan = user32.MapVirtualKeyExW(vk, 0, hkl)
    buf = ctypes.create_unicode_buffer(8)
    # Flag 0x4: do not touch the keyboard state (no dead-key side effects).
    count = user32.ToUnicodeEx(vk, scan, state, buf, len(buf), 0x4, hkl)
    if count > 0:
        text = buf.value[:count]
        if text.strip() and text.isprintable():
            return text
    return None
