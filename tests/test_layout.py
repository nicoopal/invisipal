"""Tests for the pure geometry helpers."""

from __future__ import annotations

import pytest

from invisipal.layout import SNAP_POSITIONS, key_color, snap_position

WORK = (0, 0, 1920, 1040)  # 1080p screen minus a 40 px taskbar
SIZE = (600, 400)


@pytest.mark.parametrize(
    ("where", "expected"),
    [
        ("top_left", (16, 16)),
        ("top_center", (660, 16)),
        ("top_right", (1304, 16)),
        ("bottom_left", (16, 624)),
        ("bottom_center", (660, 624)),
        ("bottom_right", (1304, 624)),
    ],
)
def test_snap_positions(where, expected):
    assert snap_position(WORK, SIZE, where) == expected


def test_snap_respects_monitor_offset_and_margin():
    second_monitor = (1920, 0, 3840, 1080)
    assert snap_position(second_monitor, SIZE, "top_left", margin=0) == (1920, 0)
    assert snap_position(second_monitor, SIZE, "bottom_right", margin=0) == (3240, 680)


def test_snap_never_starts_off_screen():
    assert snap_position((0, 0, 500, 300), (800, 600), "bottom_right") == (0, 0)


def test_unknown_position():
    with pytest.raises(ValueError):
        snap_position(WORK, SIZE, "middle")


def test_all_positions_listed():
    assert len(SNAP_POSITIONS) == 6


@pytest.mark.parametrize(("bg", "key"), [("#14161b", "#14161c"), ("#0000ff", "#0000fe"), ("#FFFFFF", "#fffffe")])
def test_key_color_is_one_step_away(bg, key):
    assert key_color(bg) == key
