"""Tests for the Python-version setup helpers (no shortcuts are created here)."""

from __future__ import annotations

import json
from pathlib import Path

from invisipal import installer


def make_source(tmp_path: Path) -> Path:
    src = tmp_path / "zip" / "Invisipal"
    (src / "invisipal" / "assets").mkdir(parents=True)
    (src / "invisipal" / "__init__.py").write_text('__version__ = "9.9.9"\n', encoding="utf-8")
    (src / "invisipal" / "assets" / "invisipal.ico").write_bytes(b"ico")
    (src / "invisipal" / "__pycache__").mkdir()
    (src / "invisipal" / "__pycache__" / "x.pyc").write_bytes(b"junk")
    (src / "invisipal.pyw").write_text("print('hi')\n", encoding="utf-8")
    (src / "LICENSE").write_text("MIT\n", encoding="utf-8")
    return src


def test_copy_app_copies_program_without_caches(tmp_path):
    src, app = make_source(tmp_path), tmp_path / "app"
    installer.copy_app(src, app)
    assert (app / "invisipal.pyw").is_file()
    assert (app / "invisipal" / "assets" / "invisipal.ico").is_file()
    assert not (app / "invisipal" / "__pycache__").exists()


def test_copy_app_removes_stale_modules(tmp_path):
    src, app = make_source(tmp_path), tmp_path / "app"
    (app / "invisipal").mkdir(parents=True)
    (app / "invisipal" / "old_module.py").write_text("", encoding="utf-8")
    installer.copy_app(src, app)
    assert not (app / "invisipal" / "old_module.py").exists()


def test_copy_app_from_installed_copy_is_a_no_op(tmp_path):
    src = make_source(tmp_path)
    installer.copy_app(src, src)
    assert (src / "invisipal" / "__init__.py").is_file()


def test_shortcut_env(tmp_path):
    app = tmp_path / "app"
    env = installer.shortcut_env(app, ["Programs", "Desktop"], pythonw=Path("C:/Python/pythonw.exe"))
    assert env["INV_PLACES"] == "Programs,Desktop"
    assert env["INV_ACTION"] == "create"
    assert env["INV_ARGS"] == f'"{app / "invisipal.pyw"}"'
    assert env["INV_ICON"].endswith("invisipal.ico")


def test_pythonw_path_prefers_windowless_interpreter(tmp_path):
    (tmp_path / "python.exe").write_bytes(b"")
    (tmp_path / "pythonw.exe").write_bytes(b"")
    assert installer.pythonw_path(str(tmp_path / "python.exe")) == tmp_path / "pythonw.exe"


def test_pythonw_path_falls_back_to_current(tmp_path):
    (tmp_path / "python.exe").write_bytes(b"")
    assert installer.pythonw_path(str(tmp_path / "python.exe")) == tmp_path / "python.exe"


def test_store_python_detection():
    assert installer.is_store_python(r"C:\Users\x\AppData\Local\Microsoft\WindowsApps\python.exe")
    assert not installer.is_store_python(r"C:\Program Files\Python313\python.exe")


def test_install_and_uninstall_with_marker(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(installer, "run_shortcut_script",
                        lambda env: calls.append((env["INV_ACTION"], env["INV_PLACES"])))
    src, app = make_source(tmp_path), tmp_path / "app"
    installer.install(["Programs"], source=src, app=app)
    assert json.loads((app / "install.json").read_text(encoding="utf-8"))["shortcuts"] == ["Programs"]
    assert calls == [("remove", "Programs,Desktop,Startup"), ("create", "Programs")]
    installer.uninstall(app)
    assert not app.exists()


def test_uninstall_never_deletes_unknown_folders(tmp_path, monkeypatch):
    monkeypatch.setattr(installer, "run_shortcut_script", lambda env: None)
    folder = tmp_path / "not-ours"
    folder.mkdir()
    installer.uninstall(folder)
    assert folder.exists()
