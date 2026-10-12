"""The skill's standalone checker must split guides exactly like the app."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from invisipal import cards

ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "skills" / "invisipal-cards" / "scripts" / "check_guide.py"

spec = importlib.util.spec_from_file_location("check_guide", CHECKER)
check_guide = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_guide)

SAMPLES = [
    "# A\n\ntext\n\n---\n\n## B\n- x\n- y\n",
    "# One\nbody\n## Two\nmore\n# Three\n",
    "para one\nstill one\n\npara two\n\n\npara three",
    "```\n---\n```\n\n---\n\n## after fence",
    "\n\n---\n\n## only\n\n---\n\n",
    "pre\n## H1\nx\n## H2\n```\n## not a heading\n```\n",
]


EXAMPLES = [p.read_text(encoding="utf-8") for p in (ROOT / "invisipal" / "examples").glob("*.*")]


@pytest.mark.parametrize("text", SAMPLES + EXAMPLES)
def test_same_cards_and_titles_as_app(text):
    app_cards = cards.split_cards(text)
    _, checker_cards = check_guide.split_cards(text)
    assert [c.title for c in app_cards] == [check_guide.make_title(lines) for _, lines in checker_cards]
    assert [c.text for c in app_cards] == ["\n".join(lines) for _, lines in checker_cards]


def test_flags_unrenderable_syntax():
    result = check_guide.check("## Card\n| a | b |\n[x](http://y)\nhi \U0001f44b\n<b>bold</b>\n")
    assert len(result["errors"]) == 4


def test_clean_guide_has_no_errors():
    result = check_guide.check("## Opening\n- Thanks\n- **Goal:** pilot\n\n---\n\n## Close\n> The ask\n")
    assert result["errors"] == [] and result["warnings"] == []
