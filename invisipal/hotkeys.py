"""System-wide hotkeys via ``RegisterHotKey``.

Hotkeys are registered from a dedicated background thread that runs its own
Win32 message loop, so they fire even when the Invisipal window has no focus
(or is hidden). Actions are handed back to the UI thread through a callback
that must be thread-safe (the app uses a ``queue.Queue``).
"""

from __future__ import annotations

import ctypes
import re
import threading
from collections.abc import Callable
from ctypes import wintypes
from dataclasses import dataclass

from . import win32

MODIFIERS = {
    "ctrl": win32.MOD_CONTROL,
    "control": win32.MOD_CONTROL,
    "alt": win32.MOD_ALT,
    "shift": win32.MOD_SHIFT,
    "win": win32.MOD_WIN,
}

NAMED_KEYS = {
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "pageup": 0x21, "pgup": 0x21, "pagedown": 0x22, "pgdn": 0x22,
    "end": 0x23, "home": 0x24, "insert": 0x2D, "ins": 0x2D,
    "delete": 0x2E, "del": 0x2E, "space": 0x20, "enter": 0x0D,
    "tab": 0x09, "esc": 0x1B, "escape": 0x1B, "backspace": 0x08,
    "plus": 0xBB, "+": 0xBB, "=": 0xBB, "minus": 0xBD, "-": 0xBD, "comma": 0xBC, "period": 0xBE,
    "numadd": 0x6B, "numsub": 0x6D, "nummul": 0x6A, "numdiv": 0x6F,
}
NAMED_KEYS.update({f"f{n}": 0x6F + n for n in range(1, 25)})
NAMED_KEYS.update({f"num{n}": 0x60 + n for n in range(10)})

# Actions where holding the key down should keep repeating.
REPEATABLE = {"font_up", "font_down", "opacity_up", "opacity_down"}


class HotkeyError(ValueError):
    pass


@dataclass(frozen=True)
class Hotkey:
    action: str
    text: str
    modifiers: int
    vk: int


def parse_hotkey(text: str) -> tuple[int, int]:
    """Parse ``"Ctrl+Alt+Right"`` into ``(modifiers, virtual_key)``."""
    # "+" or "-" separate parts; a trailing one is the key itself ("Ctrl+Alt+-").
    parts = [p.strip().lower() for p in re.split(r"[+-](?=.)", text.strip()) if p.strip()]
    if not parts:
        raise HotkeyError("empty hotkey")
    *mods, key = parts
    modifiers = 0
    for mod in mods:
        if mod not in MODIFIERS:
            raise HotkeyError(f"unknown modifier '{mod}' in '{text}'")
        modifiers |= MODIFIERS[mod]
    if key in NAMED_KEYS:
        vk = NAMED_KEYS[key]
    elif len(key) == 1 and key.isascii() and key.isalnum():
        vk = ord(key.upper())
    else:
        raise HotkeyError(f"unknown key '{key}' in '{text}'")
    if not modifiers:
        raise HotkeyError(f"'{text}' needs at least one modifier (Ctrl/Alt/Shift/Win)")
    return modifiers, vk


def build_hotkeys(bindings: dict[str, str]) -> tuple[list[Hotkey], list[str]]:
    """Turn the config mapping into Hotkey objects, collecting parse errors."""
    hotkeys, errors = [], []
    for action, text in bindings.items():
        if not text:
            continue  # empty string disables the hotkey
        try:
            mods, vk = parse_hotkey(text)
        except HotkeyError as exc:
            errors.append(f"{action}: {exc}")
            continue
        if action not in REPEATABLE:
            mods |= win32.MOD_NOREPEAT
        hotkeys.append(Hotkey(action, text, mods, vk))
    return hotkeys, errors


def resolve_altgr_conflicts(hotkeys: list[Hotkey], fix: bool = True) -> tuple[list[Hotkey], list[str]]:
    """Handle Ctrl+Alt+<key> combos that also type a character via AltGr.

    Windows reports AltGr as Ctrl+Alt, so registering e.g. Ctrl+Alt+Q globally
    would stop "@" from working on Latin American / German keyboards. With
    ``fix`` the hotkey gets an extra Shift (Ctrl+Alt+Shift+Q) instead.
    """
    result, notes = [], []
    for hk in hotkeys:
        base = hk.modifiers & ~win32.MOD_NOREPEAT
        char = win32.ctrl_alt_produces_char(hk.vk) if base == (win32.MOD_CONTROL | win32.MOD_ALT) else None
        if char and fix:
            text = hk.text.rsplit("+", 1)
            moved = Hotkey(hk.action, f"{text[0]}+Shift+{text[1]}", hk.modifiers | win32.MOD_SHIFT, hk.vk)
            notes.append(f"{hk.text} types '{char}' (AltGr) on your keyboard, so {moved.text} is used instead")
            result.append(moved)
        else:
            if char:
                notes.append(f"{hk.text} also types '{char}' (AltGr) on your keyboard")
            result.append(hk)
    return result, notes


class HotkeyThread(threading.Thread):
    """Owns the hotkey registrations and a tiny Win32 message loop."""

    def __init__(self, hotkeys: list[Hotkey], on_action: Callable[[str], None], wake_event=None):
        super().__init__(name="invisipal-hotkeys", daemon=True)
        self.hotkeys = hotkeys
        self.on_action = on_action
        self.wake_event = wake_event  # named event: "another instance asked us to show up"
        self.failed: list[str] = []
        self.ready = threading.Event()
        self._thread_id = 0

    def run(self) -> None:
        user32 = win32.user32
        self._thread_id = win32.kernel32.GetCurrentThreadId()
        msg = wintypes.MSG()
        # Force creation of this thread's message queue before anyone posts to it.
        user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, win32.PM_NOREMOVE)

        actions: dict[int, str] = {}
        for index, hk in enumerate(self.hotkeys, start=1):
            if user32.RegisterHotKey(None, index, hk.modifiers, hk.vk):
                actions[index] = hk.action
            else:
                self.failed.append(hk.text)
        self.ready.set()

        handles = (wintypes.HANDLE * 1)(self.wake_event) if self.wake_event else None
        count = 1 if handles else 0
        try:
            while True:
                result = user32.MsgWaitForMultipleObjects(
                    count, handles, False, win32.INFINITE, win32.QS_ALLINPUT
                )
                if count and result == win32.WAIT_OBJECT_0:
                    self.on_action("show")
                    continue
                while user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, win32.PM_REMOVE):
                    if msg.message == win32.WM_QUIT:
                        return
                    if msg.message == win32.WM_HOTKEY and msg.wParam in actions:
                        self.on_action(actions[msg.wParam])
        finally:
            for index in actions:
                user32.UnregisterHotKey(None, index)

    def stop(self) -> None:
        if self._thread_id:
            win32.user32.PostThreadMessageW(self._thread_id, win32.WM_QUIT, 0, 0)
        self.join(timeout=1.0)
