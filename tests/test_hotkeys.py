from __future__ import annotations

import pytest

from invisipal import win32
from invisipal.hotkeys import (
    REPEATABLE,
    Hotkey,
    HotkeyError,
    build_hotkeys,
    parse_hotkey,
    resolve_altgr_conflicts,
)

CTRL_ALT = win32.MOD_CONTROL | win32.MOD_ALT


class TestParseHotkey:
    def test_ctrl_alt_right(self):
        assert parse_hotkey("Ctrl+Alt+Right") == (CTRL_ALT, 0x27)

    @pytest.mark.parametrize("text", ["ctrl+alt+right", "CTRL+ALT+RIGHT", "Ctrl + Alt + Right", "ctrl-alt-right"])
    def test_case_and_spacing_insensitive(self, text):
        assert parse_hotkey(text) == (CTRL_ALT, 0x27)

    def test_control_alias_and_other_modifiers(self):
        mods, _ = parse_hotkey("Control+Shift+Win+Alt+A")
        assert mods == win32.MOD_CONTROL | win32.MOD_SHIFT | win32.MOD_WIN | win32.MOD_ALT

    @pytest.mark.parametrize("n", [1, 5, 12, 24])
    def test_function_keys(self, n):
        assert parse_hotkey(f"Ctrl+F{n}") == (win32.MOD_CONTROL, 0x6F + n)

    def test_f1_is_vk_f1(self):
        assert parse_hotkey("Alt+F1")[1] == 0x70

    @pytest.mark.parametrize("key, vk", [("a", 0x41), ("Q", 0x51), ("z", 0x5A), ("0", 0x30), ("9", 0x39)])
    def test_letters_and_digits(self, key, vk):
        assert parse_hotkey(f"Ctrl+Alt+{key}") == (CTRL_ALT, vk)

    @pytest.mark.parametrize(
        "name, vk",
        [("PageUp", 0x21), ("PgUp", 0x21), ("PageDown", 0x22), ("PgDn", 0x22),
         ("Home", 0x24), ("End", 0x23), ("Delete", 0x2E), ("Del", 0x2E), ("Esc", 0x1B), ("Space", 0x20)],
    )
    def test_named_keys_and_aliases(self, name, vk):
        assert parse_hotkey(f"Ctrl+Alt+{name}") == (CTRL_ALT, vk)

    def test_numpad_keys(self):
        assert parse_hotkey("Ctrl+Num5")[1] == 0x65

    def test_unknown_modifier(self):
        with pytest.raises(HotkeyError, match="unknown modifier 'hyper'"):
            parse_hotkey("Hyper+Alt+A")

    @pytest.mark.parametrize("text", ["Ctrl+Alt+Banana", "Ctrl+é", "Ctrl+Alt+F25", "Ctrl+!"])
    def test_unknown_key(self, text):
        with pytest.raises(HotkeyError, match="unknown key"):
            parse_hotkey(text)

    @pytest.mark.parametrize("text", ["A", "Right", "F5", "+", "-"])
    def test_missing_modifier(self, text):
        with pytest.raises(HotkeyError, match="at least one modifier"):
            parse_hotkey(text)

    @pytest.mark.parametrize("text", ["", "  "])
    def test_empty(self, text):
        with pytest.raises(HotkeyError, match="empty"):
            parse_hotkey(text)

    def test_hotkey_error_is_value_error(self):
        assert issubclass(HotkeyError, ValueError)


class TestBuildHotkeys:
    def test_builds_and_adds_norepeat(self):
        hotkeys, errors = build_hotkeys({"next": "Ctrl+Alt+Right"})
        assert errors == []
        (hk,) = hotkeys
        assert hk == Hotkey("next", "Ctrl+Alt+Right", CTRL_ALT | win32.MOD_NOREPEAT, 0x27)

    def test_repeatable_actions_do_not_get_norepeat(self):
        bindings = {action: "Ctrl+Alt+Up" for action in REPEATABLE}
        hotkeys, _ = build_hotkeys(bindings)
        assert len(hotkeys) == len(REPEATABLE)
        assert all(not hk.modifiers & win32.MOD_NOREPEAT for hk in hotkeys)

    def test_non_repeatable_get_norepeat(self):
        hotkeys, _ = build_hotkeys({"quit": "Ctrl+Alt+Q", "toggle": "Ctrl+Alt+H"})
        assert all(hk.modifiers & win32.MOD_NOREPEAT for hk in hotkeys)

    def test_empty_string_disables_binding(self):
        hotkeys, errors = build_hotkeys({"next": "", "prev": "Ctrl+Alt+Left"})
        assert [hk.action for hk in hotkeys] == ["prev"]
        assert errors == []

    def test_errors_are_collected_and_others_kept(self):
        hotkeys, errors = build_hotkeys({"a": "Ctrl+Alt+Nope", "b": "Q", "c": "Ctrl+Alt+Q"})
        assert [hk.action for hk in hotkeys] == ["c"]
        assert len(errors) == 2
        assert errors[0].startswith("a: ")
        assert errors[1].startswith("b: ")

    def test_default_config_hotkeys_all_valid(self):
        from invisipal.config import DEFAULTS

        hotkeys, errors = build_hotkeys(DEFAULTS["hotkeys"])
        assert errors == []
        assert len(hotkeys) == len(DEFAULTS["hotkeys"])
        # No two defaults may collide.
        assert len({(hk.modifiers & ~win32.MOD_NOREPEAT, hk.vk) for hk in hotkeys}) == len(hotkeys)


class TestAltGrConflicts:
    @pytest.fixture
    def q_types_at(self, monkeypatch):
        """Simulate a keyboard layout where AltGr+Q types '@'."""
        monkeypatch.setattr(win32, "ctrl_alt_produces_char", lambda vk: "@" if vk == ord("Q") else None)

    def test_fix_adds_shift(self, q_types_at):
        hotkeys, _ = build_hotkeys({"quit": "Ctrl+Alt+Q", "toggle": "Ctrl+Alt+H"})
        fixed, notes = resolve_altgr_conflicts(hotkeys, fix=True)
        quit_hk, toggle_hk = fixed
        assert quit_hk.text == "Ctrl+Alt+Shift+Q"
        assert quit_hk.modifiers == CTRL_ALT | win32.MOD_SHIFT | win32.MOD_NOREPEAT
        assert quit_hk.vk == ord("Q") and quit_hk.action == "quit"
        assert toggle_hk == hotkeys[1]  # untouched
        assert len(notes) == 1
        assert "'@'" in notes[0] and "Ctrl+Alt+Shift+Q" in notes[0]

    def test_fixed_text_still_parses_to_same_modifiers(self, q_types_at):
        hotkeys, _ = build_hotkeys({"quit": "Ctrl+Alt+Q"})
        (fixed,), _ = resolve_altgr_conflicts(hotkeys, fix=True)
        mods, vk = parse_hotkey(fixed.text)
        assert mods | win32.MOD_NOREPEAT == fixed.modifiers
        assert vk == fixed.vk

    def test_warn_only_without_fix(self, q_types_at):
        hotkeys, _ = build_hotkeys({"quit": "Ctrl+Alt+Q"})
        result, notes = resolve_altgr_conflicts(hotkeys, fix=False)
        assert result == hotkeys
        assert len(notes) == 1
        assert "also types '@'" in notes[0]

    def test_no_conflict_no_notes(self, monkeypatch):
        monkeypatch.setattr(win32, "ctrl_alt_produces_char", lambda vk: None)
        hotkeys, _ = build_hotkeys({"quit": "Ctrl+Alt+Q"})
        result, notes = resolve_altgr_conflicts(hotkeys)
        assert result == hotkeys and notes == []

    def test_only_plain_ctrl_alt_combos_are_checked(self, monkeypatch):
        monkeypatch.setattr(win32, "ctrl_alt_produces_char", lambda vk: "@")
        hotkeys, _ = build_hotkeys({"a": "Ctrl+Shift+Q", "b": "Alt+Q", "c": "Ctrl+Alt+Shift+Q"})
        result, notes = resolve_altgr_conflicts(hotkeys)
        assert result == hotkeys and notes == []

    def test_repeatable_hotkey_without_norepeat_is_still_checked(self, monkeypatch):
        monkeypatch.setattr(win32, "ctrl_alt_produces_char", lambda vk: "€")
        hotkeys, _ = build_hotkeys({"font_up": "Ctrl+Alt+E"})
        (fixed,), notes = resolve_altgr_conflicts(hotkeys)
        assert fixed.text == "Ctrl+Alt+Shift+E"
        assert not fixed.modifiers & win32.MOD_NOREPEAT
        assert notes


@pytest.mark.parametrize(
    ("text", "vk"),
    [("Ctrl+Alt+-", 0xBD), ("Ctrl+Alt++", 0xBB), ("Ctrl-Alt-Minus", 0xBD), ("Ctrl+Alt+=", 0xBB)],
)
def test_plus_and_minus_keys(text, vk):
    assert parse_hotkey(text) == (win32.MOD_CONTROL | win32.MOD_ALT, vk)
