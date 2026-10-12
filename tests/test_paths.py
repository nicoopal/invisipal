"""Tests for the data-folder resolution and first-run seeding."""

from __future__ import annotations

from pathlib import Path

from invisipal import paths


def make_app(tmp_path: Path) -> Path:
    app = tmp_path / "app"
    (app / "guides").mkdir(parents=True)
    (app / "guides" / "guia.txt").write_text("# Hola", encoding="utf-8")
    (app / "guides" / "demo-meeting.md").write_text("# Demo", encoding="utf-8")
    (app / "guides" / "notes.docx").write_text("not a guide", encoding="utf-8")
    return app


class TestResolveDataDir:
    def test_defaults_to_documents_invisipal(self, tmp_path, monkeypatch):
        monkeypatch.setattr(paths, "documents_dir", lambda: tmp_path / "Docs")
        assert paths.resolve_data_dir(app=make_app(tmp_path)) == tmp_path / "Docs" / "Invisipal"

    def test_portable_marker_keeps_data_next_to_app(self, tmp_path):
        app = make_app(tmp_path)
        (app / "portable").write_text("", encoding="utf-8")
        assert paths.resolve_data_dir(app=app) == app

    def test_override_wins(self, tmp_path):
        app = make_app(tmp_path)
        (app / "portable").write_text("", encoding="utf-8")
        assert paths.resolve_data_dir(tmp_path / "custom", app=app) == (tmp_path / "custom").resolve()

    def test_documents_dir_falls_back_to_home(self, monkeypatch):
        monkeypatch.setattr(paths.win32, "documents_folder", lambda: None)
        assert paths.documents_dir() == Path.home() / "Documents"


class TestPrepareDataDir:
    def test_first_run_seeds_example_guides(self, tmp_path, monkeypatch):
        monkeypatch.setattr(paths, "EXAMPLES_DIR", tmp_path / "no-examples")
        app, data = make_app(tmp_path), tmp_path / "Docs" / "Invisipal"
        notes = paths.prepare_data_dir(data, app=app)
        assert sorted(p.name for p in (data / "guides").iterdir()) == ["demo-meeting.md", "guia.txt"]
        assert len(notes) == 2

    def test_migrates_old_config(self, tmp_path):
        app, data = make_app(tmp_path), tmp_path / "data"
        (app / "config.json").write_text('{"font_size": 30}', encoding="utf-8")
        paths.prepare_data_dir(data, app=app)
        assert (data / "config.json").read_text(encoding="utf-8") == '{"font_size": 30}'

    def test_does_not_reseed_existing_folder(self, tmp_path):
        app, data = make_app(tmp_path), tmp_path / "data"
        (data / "guides").mkdir(parents=True)
        assert paths.prepare_data_dir(data, app=app) == []
        assert list((data / "guides").iterdir()) == []

    def test_existing_config_is_not_overwritten(self, tmp_path):
        app, data = make_app(tmp_path), tmp_path / "data"
        (app / "config.json").write_text('{"font_size": 30}', encoding="utf-8")
        data.mkdir()
        (data / "config.json").write_text('{"font_size": 12}', encoding="utf-8")
        paths.prepare_data_dir(data, app=app)
        assert (data / "config.json").read_text(encoding="utf-8") == '{"font_size": 12}'

    def test_portable_mode_with_existing_guides_is_untouched(self, tmp_path):
        app = make_app(tmp_path)
        assert paths.prepare_data_dir(app, app=app) == []

    def test_portable_mode_first_run_gets_examples(self, tmp_path, monkeypatch):
        examples = tmp_path / "examples"
        examples.mkdir()
        (examples / "guia.txt").write_text("# Ejemplo", encoding="utf-8")
        monkeypatch.setattr(paths, "EXAMPLES_DIR", examples)
        app = tmp_path / "portable-app"
        app.mkdir()
        paths.prepare_data_dir(app, app=app)
        assert (app / "guides" / "guia.txt").read_text(encoding="utf-8") == "# Ejemplo"

    def test_bundled_examples_exist(self):
        names = {p.name for p in paths.EXAMPLES_DIR.iterdir()}
        assert {"guia.txt", "demo-meeting.md"} <= names

    def test_examples_win_over_legacy_copies(self, tmp_path, monkeypatch):
        examples = tmp_path / "examples"
        examples.mkdir()
        (examples / "guia.txt").write_text("# New example", encoding="utf-8")
        monkeypatch.setattr(paths, "EXAMPLES_DIR", examples)
        app, data = make_app(tmp_path), tmp_path / "data"
        paths.prepare_data_dir(data, app=app)
        assert (data / "guides" / "guia.txt").read_text(encoding="utf-8") == "# New example"
        assert (data / "guides" / "demo-meeting.md").exists()  # personal/legacy file still copied
