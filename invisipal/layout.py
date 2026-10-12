"""Pure geometry helpers (no Tk, no Win32), so they are easy to test."""

from __future__ import annotations

SNAP_POSITIONS = ("top_left", "top_center", "top_right", "bottom_left", "bottom_center", "bottom_right")


def snap_position(work: tuple[int, int, int, int], size: tuple[int, int], where: str,
                  margin: int = 16) -> tuple[int, int]:
    """Top-left corner that puts a window of ``size`` at ``where`` inside ``work``.

    ``work`` is the monitor's work area (left, top, right, bottom), i.e. the
    screen minus the taskbar. The window keeps its size and is clamped so it
    never starts off-screen.
    """
    if where not in SNAP_POSITIONS:
        raise ValueError(f"unknown position {where!r}")
    left, top, right, bottom = work
    width, height = size
    vertical, horizontal = where.split("_")
    x = {
        "left": left + margin,
        "center": left + (right - left - width) // 2,
        "right": right - margin - width,
    }[horizontal]
    y = top + margin if vertical == "top" else bottom - margin - height
    return max(left, x), max(top, y)


def key_color(background: str) -> str:
    """A color one step away from ``background`` to use as the transparency key.

    Pixels of exactly this color become fully transparent. Anti-aliased text
    edges blend toward it, so keeping it next to the real background avoids
    colored fringes.
    """
    value = background.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    b = b + 1 if b < 255 else b - 1
    return f"#{r:02x}{g:02x}{b:02x}"
