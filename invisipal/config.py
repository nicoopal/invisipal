"""Settings persisted to ``config.json`` next to the script (or the .exe)."""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    # Window
    "x": None,
    "y": None,
    "width": 620,
    "height": 440,
    "opacity": 0.85,
    "always_on_top": True,
    "show_in_taskbar": False,
    "capture_protection": True,
    # Text
    "font_family": "Segoe UI",
    "mono_family": "Cascadia Mono",
    "font_size": 20,
    "line_spacing": 1.5,
    # Content
    "guides_dir": "guides",
    "current_guide": "guia.txt",
    "split_mode": "auto",
    "auto_reload": True,
    "positions": {},
    # Global hotkeys ("" disables one)
    "avoid_altgr_conflicts": True,
    "hotkeys": {
        "next": "Ctrl+Alt+Right",
        "prev": "Ctrl+Alt+Left",
        "font_up": "Ctrl+Alt+Up",
        "font_down": "Ctrl+Alt+Down",
        "toggle": "Ctrl+Alt+H",
        "reload": "Ctrl+Alt+R",
        "quit": "Ctrl+Alt+Q",
        "first": "Ctrl+Alt+Home",
        "last": "Ctrl+Alt+End",
        "opacity_up": "Ctrl+Alt+PageUp",
        "opacity_down": "Ctrl+Alt+PageDown",
        "click_through": "Ctrl+Alt+T",
        "next_guide": "Ctrl+Alt+G",
        "timer": "Ctrl+Alt+S",
    },
    # Colors
    "theme": {
        "background": "#14161b",
        "surface": "#1b1e25",
        "border": "#2a2f3a",
        "text": "#e7e9ee",
        "muted": "#8a93a6",
        "heading": "#ffffff",
        "accent": "#7aa2f7",
        "code_bg": "#232733",
        "code_fg": "#b8e186",
        "quote": "#a9b4d0",
        "highlight_bg": "#5a4a12",
        "highlight_fg": "#ffe08a",
        "ok": "#73d0a0",
        "warn": "#f2b45a",
        "danger": "#f7768e",
    },
}

FONT_MIN, FONT_MAX = 9, 96
OPACITY_MIN, OPACITY_MAX = 0.15, 1.0
SPLIT_MODES = ("auto", "separator", "heading", "paragraph", "none")


def _merge(defaults: dict, user: dict) -> dict:
    """Recursively overlay user values on top of the defaults."""
    result = copy.deepcopy(defaults)
    for key, value in user.items():
        if isinstance(result.get(key), dict) and key != "positions":
            if isinstance(value, dict):  # ignore e.g. "hotkeys": null
                result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _clamp(value, low, high, fallback):
    try:
        return max(low, min(high, type(fallback)(value)))
    except (TypeError, ValueError):
        return fallback


def sanitize(cfg: dict) -> dict:
    cfg["font_size"] = _clamp(cfg["font_size"], FONT_MIN, FONT_MAX, DEFAULTS["font_size"])
    cfg["opacity"] = _clamp(cfg["opacity"], OPACITY_MIN, OPACITY_MAX, DEFAULTS["opacity"])
    cfg["width"] = _clamp(cfg["width"], 280, 10000, DEFAULTS["width"])
    cfg["height"] = _clamp(cfg["height"], 160, 10000, DEFAULTS["height"])
    cfg["line_spacing"] = _clamp(cfg["line_spacing"], 1.0, 3.0, DEFAULTS["line_spacing"])
    if cfg["split_mode"] not in SPLIT_MODES:
        cfg["split_mode"] = "auto"
    if not isinstance(cfg.get("positions"), dict):
        cfg["positions"] = {}
    return cfg


class Config:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data: dict[str, Any] = copy.deepcopy(DEFAULTS)
        self.load_error: str | None = None

    def load(self) -> Config:
        if self.path.exists():
            try:
                user = json.loads(self.path.read_text(encoding="utf-8-sig"))
                if isinstance(user, dict):
                    self.data = _merge(DEFAULTS, user)
            except (OSError, json.JSONDecodeError) as exc:
                # Keep the broken file around: the next save would overwrite it.
                backup = self.path.with_name("config.broken.json")
                try:
                    os.replace(self.path, backup)
                except OSError:
                    pass
                self.load_error = f"config.json was invalid ({exc}); moved to {backup.name}"
        self.data = sanitize(self.data)
        return self

    def save(self) -> None:
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self.data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        os.replace(tmp, self.path)

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.data[key] = value
