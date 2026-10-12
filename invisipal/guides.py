"""A folder of guide files (``.md`` / ``.txt``): one file per meeting."""

from __future__ import annotations

import os
import re
from pathlib import Path

GUIDE_EXTENSIONS = (".md", ".txt", ".markdown")
_INVALID_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]+')

NEW_GUIDE_TEMPLATE = """# {title}

Write your first card here.

---

## Second card

- Paste anything: plain text, Markdown, bullet lists
- A line with only `---` starts a new card
"""


def safe_filename(name: str, default_ext: str = ".md") -> str:
    name = _INVALID_CHARS.sub("-", name).strip(" .-") or "guide"
    if not name.lower().endswith(GUIDE_EXTENSIONS):
        name += default_ext
    return name


class GuideLibrary:
    def __init__(self, folder: Path):
        self.folder = Path(folder)

    def ensure(self) -> None:
        self.folder.mkdir(parents=True, exist_ok=True)

    def names(self) -> list[str]:
        if not self.folder.is_dir():
            return []
        files = [p for p in self.folder.iterdir() if p.is_file() and p.suffix.lower() in GUIDE_EXTENSIONS]
        return sorted((p.name for p in files), key=str.lower)

    def path(self, name: str) -> Path:
        return self.folder / name

    def exists(self, name: str) -> bool:
        return self.path(name).is_file()

    def mtime(self, name: str) -> float:
        try:
            return self.path(name).stat().st_mtime
        except OSError:
            return 0.0

    def read(self, name: str) -> str:
        return self.path(name).read_text(encoding="utf-8-sig", errors="replace")

    def write(self, name: str, text: str) -> None:
        self.ensure()
        target = self.path(name)
        tmp = target.with_name(target.name + ".tmp")
        tmp.write_text(text, encoding="utf-8")
        os.replace(tmp, target)

    def unique_name(self, wanted: str) -> str:
        name = safe_filename(wanted)
        stem, ext = os.path.splitext(name)
        counter = 2
        while self.exists(name):
            name = f"{stem}-{counter}{ext}"
            counter += 1
        return name

    def create(self, wanted: str, text: str | None = None) -> str:
        name = self.unique_name(wanted)
        title = os.path.splitext(name)[0].replace("-", " ").replace("_", " ").strip().capitalize()
        self.write(name, text if text is not None else NEW_GUIDE_TEMPLATE.format(title=title))
        return name
