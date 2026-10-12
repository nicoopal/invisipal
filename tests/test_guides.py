from __future__ import annotations

import pytest

from invisipal.guides import NEW_GUIDE_TEMPLATE, GuideLibrary, safe_filename


class TestSafeFilename:
    def test_adds_default_extension(self):
        assert safe_filename("meeting") == "meeting.md"

    @pytest.mark.parametrize("name", ["a.md", "a.txt", "a.markdown", "A.MD", "A.TXT"])
    def test_keeps_known_extensions(self, name):
        assert safe_filename(name) == name

    def test_custom_default_extension(self):
        assert safe_filename("x", ".txt") == "x.txt"

    def test_unknown_extension_gets_default_appended(self):
        assert safe_filename("notes.docx") == "notes.docx.md"

    def test_invalid_chars_sanitised(self):
        name = safe_filename('a<b>c:d"e/f\\g|h?i*j')
        assert name == "a-b-c-d-e-f-g-h-i-j.md"
        assert not set('<>:"/\\|?*') & set(name)

    def test_control_chars_sanitised(self):
        assert safe_filename("a\x00b\nc") == "a-b-c.md"

    def test_empty_or_junk_falls_back(self):
        assert safe_filename("") == "guide.md"
        assert safe_filename("  ..  ") == "guide.md"
        assert safe_filename("///") == "guide.md"

    def test_strips_outer_dots_spaces_dashes(self):
        assert safe_filename(" .name. ") == "name.md"

    def test_path_traversal_is_neutralised(self):
        name = safe_filename("../../evil")
        assert "/" not in name and "\\" not in name


class TestLibrary:
    def test_names_empty_for_missing_folder(self, tmp_path):
        assert GuideLibrary(tmp_path / "nope").names() == []

    def test_names_filters_and_sorts_case_insensitively(self, tmp_path):
        for n in ["b.md", "A.txt", "c.markdown", "image.png", "notes.docx", "d.md.tmp", "Z.MD"]:
            (tmp_path / n).write_text("x", encoding="utf-8")
        (tmp_path / "sub.md").mkdir()  # directories are ignored
        assert GuideLibrary(tmp_path).names() == ["A.txt", "b.md", "c.markdown", "Z.MD"]

    def test_ensure_creates_folder(self, tmp_path):
        lib = GuideLibrary(tmp_path / "x" / "guides")
        lib.ensure()
        assert lib.folder.is_dir()

    def test_exists_and_path(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        assert not lib.exists("a.md")
        (tmp_path / "a.md").write_text("x", encoding="utf-8")
        assert lib.exists("a.md")
        assert lib.path("a.md") == tmp_path / "a.md"

    def test_mtime(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        assert lib.mtime("missing.md") == 0.0
        (tmp_path / "a.md").write_text("x", encoding="utf-8")
        assert lib.mtime("a.md") > 0

    def test_read_strips_bom(self, tmp_path):
        (tmp_path / "a.md").write_bytes(b"\xef\xbb\xbf# Hola\n")
        assert GuideLibrary(tmp_path).read("a.md") == "# Hola\n"

    def test_read_replaces_undecodable_bytes(self, tmp_path):
        (tmp_path / "a.md").write_bytes(b"ok \xff\xfe end")
        text = GuideLibrary(tmp_path).read("a.md")
        assert text.startswith("ok ") and text.endswith(" end")

    def test_write_creates_folder_and_is_atomic(self, tmp_path):
        lib = GuideLibrary(tmp_path / "guides")
        lib.write("a.md", "hola ñ")
        assert lib.read("a.md") == "hola ñ"
        lib.write("a.md", "second")
        assert lib.read("a.md") == "second"
        assert sorted(p.name for p in lib.folder.iterdir()) == ["a.md"]  # no leftover .tmp

    def test_write_is_utf8_without_bom(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        lib.write("a.md", "é")
        assert (tmp_path / "a.md").read_bytes() == "é".encode()

    def test_unique_name_and_create_suffixes(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        assert lib.create("Weekly") == "Weekly.md"
        assert lib.create("Weekly") == "Weekly-2.md"
        assert lib.create("Weekly") == "Weekly-3.md"
        assert lib.names() == ["Weekly-2.md", "Weekly-3.md", "Weekly.md"]

    def test_create_preserves_extension_when_numbering(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        assert lib.create("n.txt") == "n.txt"
        assert lib.create("n.txt") == "n-2.txt"

    def test_create_sanitises_name(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        name = lib.create("a/b:c")
        assert name == "a-b-c.md"
        assert lib.exists(name)

    def test_create_uses_template_with_title(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        name = lib.create("sprint_review-q3")
        assert lib.read(name) == NEW_GUIDE_TEMPLATE.format(title="Sprint review q3")

    def test_create_with_explicit_text(self, tmp_path):
        lib = GuideLibrary(tmp_path)
        name = lib.create("x", "custom")
        assert lib.read(name) == "custom"
