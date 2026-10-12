"""Entry point: ``python -m invisipal`` (or double-click ``invisipal.pyw``)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__, paths, win32
from .config import Config


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="invisipal", description=__doc__)
    parser.add_argument(
        "--data-dir",
        type=Path,
        help=r"folder for config.json and guides/ (default: Documents\Invisipal)",
    )
    parser.add_argument("--guide", help="open this guide file (name inside guides/)")
    parser.add_argument(
        "--no-protect",
        action="store_true",
        help="do NOT hide the window from screen capture (for demos and screenshots)",
    )
    parser.add_argument("--version", action="version", version=f"Invisipal {__version__}")
    args = parser.parse_args(argv)

    if not win32.IS_WINDOWS:
        print("Invisipal needs Windows 10 (2004+) or Windows 11.", file=sys.stderr)
        return 1

    wake_event = win32.claim_single_instance()
    if wake_event is None:
        return 0  # already running: it has been asked to show itself

    base = paths.resolve_data_dir(args.data_dir)
    paths.prepare_data_dir(base)
    cfg = Config(base / "config.json").load()
    if args.guide:
        cfg["current_guide"] = args.guide

    win32.enable_dpi_awareness()
    from .app import InvisipalApp  # imported late so --help works without a display

    InvisipalApp(base, cfg, wake_event, protect=False if args.no_protect else None).run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
