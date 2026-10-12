r"""Where Invisipal keeps its data.

By default everything lives in ``Documents\Invisipal`` (``config.json`` plus a
``guides`` folder), so it survives app updates and is easy to find and back
up. A ``portable`` marker file next to the app keeps the data next to the app
instead, and ``--data-dir`` overrides both.
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from . import win32
from .guides import GUIDE_EXTENSIONS

APP_FOLDER_NAME = "Invisipal"
PORTABLE_MARKER = "portable"
EXAMPLES_DIR = Path(__file__).resolve().parent / "examples"


def app_dir() -> Path:
    """Folder that contains ``invisipal.pyw`` (or ``Invisipal.exe`` when frozen)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def documents_dir() -> Path:
    found = win32.documents_folder()
    return Path(found) if found else Path.home() / "Documents"


def resolve_data_dir(override: Path | None = None, app: Path | None = None) -> Path:
    r"""Pick the data folder: ``--data-dir`` > portable marker > Documents\Invisipal."""
    app = app or app_dir()
    if override:
        return Path(override).expanduser().resolve()
    if (app / PORTABLE_MARKER).exists():
        return app
    return documents_dir() / APP_FOLDER_NAME


def prepare_data_dir(data: Path, app: Path | None = None) -> list[str]:
    """Create the data folder on first run and seed it.

    Copies the bundled example guides, plus (for people upgrading from a
    version that kept data next to the app) any guides and the ``config.json``
    found in the app folder. Seeding only happens when ``guides`` does not
    exist yet, so deleted examples never come back. Returns notes about what
    was copied.
    """
    app = app or app_dir()
    data.mkdir(parents=True, exist_ok=True)
    guides = data / "guides"
    if guides.exists():
        return []
    guides.mkdir()

    notes: list[str] = []
    legacy = app / "guides"
    for source in (EXAMPLES_DIR, legacy):
        if not source.is_dir() or source.resolve() == guides.resolve():
            continue
        for file in sorted(source.iterdir()):
            target = guides / file.name
            if file.is_file() and file.suffix.lower() in GUIDE_EXTENSIONS and not target.exists():
                shutil.copy2(file, target)
                notes.append(f"copied guide {file.name}")
    old_config = app / "config.json"
    if data.resolve() != app.resolve() and old_config.is_file() and not (data / "config.json").exists():
        shutil.copy2(old_config, data / "config.json")
        notes.append("copied config.json")
    return notes
