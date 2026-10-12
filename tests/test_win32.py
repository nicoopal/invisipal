from __future__ import annotations

import sys

import pytest

from invisipal import win32

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="needs the Win32 API")


def test_ctrl_alt_produces_char_returns_none_or_printable():
    for vk in (ord("Q"), ord("E"), ord("H")):
        result = win32.ctrl_alt_produces_char(vk)
        assert result is None or (isinstance(result, str) and result.isprintable())


def test_single_instance_returns_handle_and_second_claim_is_refused():
    name = "Local\\Invisipal.Tests.SingleInstance"
    first = win32.claim_single_instance(name)
    assert first is not None
    try:
        assert win32.claim_single_instance(name) is None
    finally:
        win32.kernel32.CloseHandle(first)


def test_capture_exclusion_smoke():
    tk = pytest.importorskip("tkinter")
    try:
        root = tk.Tk()
    except tk.TclError as exc:  # no display available
        pytest.skip(f"Tk cannot open a display: {exc}")
    try:
        root.geometry("200x100+-3000+-3000")  # keep it off-screen
        root.update()
        hwnd = win32.toplevel_hwnd(root.winfo_id())
        assert hwnd

        status = win32.set_capture_excluded(hwnd, True)
        if status == "blackout":
            pytest.skip("Windows build older than 10 2004: only WDA_MONITOR is available")
        assert status == "excluded"
        assert win32.get_display_affinity(hwnd) == win32.WDA_EXCLUDEFROMCAPTURE
        assert win32.affinity_status(hwnd, True) == "excluded"

        assert win32.set_capture_excluded(hwnd, False) == "off"
        assert win32.get_display_affinity(hwnd) == win32.WDA_NONE
        assert win32.affinity_status(hwnd, False) == "off"
        assert win32.affinity_status(hwnd, True) == "failed"
    finally:
        root.destroy()
