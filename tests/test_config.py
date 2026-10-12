from __future__ import annotations

import json

import pytest

from invisipal.config import DEFAULTS, Config


def write_cfg(tmp_path, data, **kwargs):
    path = tmp_path / "config.json"
    if isinstance(data, str):
        path.write_text(data, encoding="utf-8")
    else:
        path.write_text(json.dumps(data), encoding="utf-8", **kwargs)
    return path


def test_defaults_when_file_missing(tmp_path):
    cfg = Config(tmp_path / "config.json").load()
    assert cfg.data == DEFAULTS
    assert cfg.load_error is None


def test_defaults_are_not_shared_between_instances(tmp_path):
    a = Config(tmp_path / "a.json").load()
    a["hotkeys"]["next"] = "Ctrl+Alt+N"
    a["theme"]["accent"] = "#000000"
    b = Config(tmp_path / "b.json").load()
    assert b["hotkeys"]["next"] == DEFAULTS["hotkeys"]["next"]
    assert b["theme"]["accent"] == DEFAULTS["theme"]["accent"]


def test_partial_hotkeys_keep_the_others(tmp_path):
    cfg = Config(write_cfg(tmp_path, {"hotkeys": {"next": "Ctrl+Alt+N"}})).load()
    assert cfg["hotkeys"]["next"] == "Ctrl+Alt+N"
    for action, text in DEFAULTS["hotkeys"].items():
        if action != "next":
            assert cfg["hotkeys"][action] == text


def test_partial_theme_is_merged_and_scalars_overridden(tmp_path):
    cfg = Config(write_cfg(tmp_path, {"theme": {"accent": "#fff"}, "font_family": "Arial"})).load()
    assert cfg["theme"]["accent"] == "#fff"
    assert cfg["theme"]["background"] == DEFAULTS["theme"]["background"]
    assert cfg["font_family"] == "Arial"


def test_unknown_keys_are_preserved(tmp_path):
    cfg = Config(write_cfg(tmp_path, {"future_option": 42})).load()
    assert cfg["future_option"] == 42


def test_positions_dict_is_replaced_not_merged(tmp_path):
    cfg = Config(write_cfg(tmp_path, {"positions": {"a.md": 3}})).load()
    assert cfg["positions"] == {"a.md": 3}
    # Replacement semantics: a user-supplied dict wins entirely over any default content.
    cfg2 = Config(write_cfg(tmp_path, {"positions": {}})).load()
    assert cfg2["positions"] == {}


def test_positions_with_wrong_type_is_reset(tmp_path):
    cfg = Config(write_cfg(tmp_path, {"positions": [1, 2]})).load()
    assert cfg["positions"] == {}


@pytest.mark.parametrize(
    "key, raw, expected",
    [
        ("font_size", 1, 9),
        ("font_size", 500, 96),
        ("font_size", 24, 24),
        ("font_size", "30", 30),
        ("font_size", "big", 20),
        ("font_size", None, 20),
        ("background_opacity", -1, 0.0),
        ("background_opacity", 7, 1.0),
        ("background_opacity", 0.5, 0.5),
        ("background_opacity", "x", 0.8),
        ("text_opacity", 0.0, 0.2),
        ("text_opacity", 0.6, 0.6),
        ("index_font_size", 2, 7),
        ("index_width", 5, 60),
        ("width", 10, 280),
        ("width", 99999, 10000),
        ("height", 10, 160),
        ("height", 99999, 10000),
        ("line_spacing", 0.2, 1.0),
        ("line_spacing", 9, 3.0),
        ("line_spacing", 1.8, 1.8),
    ],
)
def test_numeric_clamping(tmp_path, key, raw, expected):
    cfg = Config(write_cfg(tmp_path, {key: raw})).load()
    assert cfg[key] == pytest.approx(expected)


def test_numeric_types_follow_defaults(tmp_path):
    cfg = Config(write_cfg(tmp_path, {"font_size": 22.9, "width": 640.0})).load()
    assert isinstance(cfg["font_size"], int)
    assert isinstance(cfg["width"], int)
    assert isinstance(cfg["background_opacity"], float)


def test_migrates_old_opacity_settings(tmp_path):
    old = {"opacity": 0.6, "hotkeys": {"opacity_up": "Ctrl+Alt+F1", "opacity_down": "Ctrl+Alt+F2"}}
    cfg = Config(write_cfg(tmp_path, old)).load()
    assert cfg["background_opacity"] == pytest.approx(0.6)
    assert "opacity" not in cfg.data
    assert cfg["hotkeys"]["background_more"] == "Ctrl+Alt+F1"
    assert cfg["hotkeys"]["background_less"] == "Ctrl+Alt+F2"
    assert "opacity_up" not in cfg["hotkeys"]


@pytest.mark.parametrize("mode", ["auto", "separator", "heading", "paragraph", "none"])
def test_valid_split_modes_kept(tmp_path, mode):
    assert Config(write_cfg(tmp_path, {"split_mode": mode})).load()["split_mode"] == mode


@pytest.mark.parametrize("mode", ["bogus", "", None, 3])
def test_invalid_split_mode_becomes_auto(tmp_path, mode):
    assert Config(write_cfg(tmp_path, {"split_mode": mode})).load()["split_mode"] == "auto"


def test_corrupted_json_falls_back_to_defaults(tmp_path):
    cfg = Config(write_cfg(tmp_path, "{ not json")).load()
    assert cfg.data == DEFAULTS
    assert cfg.load_error is not None
    assert "config.json" in cfg.load_error


def test_non_object_json_falls_back_to_defaults(tmp_path):
    cfg = Config(write_cfg(tmp_path, "[1, 2, 3]")).load()
    assert cfg.data == DEFAULTS


def test_utf8_bom_tolerated(tmp_path):
    path = tmp_path / "config.json"
    path.write_bytes(b"\xef\xbb\xbf" + json.dumps({"font_size": 31}).encode("utf-8"))
    cfg = Config(path).load()
    assert cfg["font_size"] == 31
    assert cfg.load_error is None


def test_save_load_round_trip(tmp_path):
    path = tmp_path / "config.json"
    cfg = Config(path).load()
    cfg["font_size"] = 33
    cfg["x"] = 120
    cfg["positions"] = {"ñandú.md": 4}
    cfg["hotkeys"]["quit"] = "Ctrl+Alt+Shift+Q"
    cfg.save()

    assert not path.with_suffix(".json.tmp").exists()
    assert path.read_text(encoding="utf-8").endswith("\n")
    assert "ñandú" in path.read_text(encoding="utf-8")  # ensure_ascii=False

    again = Config(path).load()
    assert again.data == cfg.data


def test_item_access(tmp_path):
    cfg = Config(tmp_path / "c.json")
    cfg["font_size"] = 40
    assert cfg["font_size"] == 40
