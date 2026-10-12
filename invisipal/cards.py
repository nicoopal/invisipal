"""Split a guide (plain text or Markdown) into cards."""

from __future__ import annotations

import re
from dataclasses import dataclass

SEPARATOR_RE = re.compile(r"^\s*-{3,}\s*$")
HEADING_SPLIT_RE = re.compile(r"^\s{0,3}#{1,2}\s+\S")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_MARKUP_RE = re.compile(r"(\*\*|__|==|~~|`|\*)")
LEADING_MARKUP_RE = re.compile(r"^\s*(#{1,6}\s+|>\s*|[-*+]\s+(\[[ xX]\]\s+)?|\d+[.)]\s+)")


@dataclass
class Card:
    text: str
    title: str


def _fence_states(lines: list[str]) -> list[bool]:
    """For each line, whether it sits inside a fenced code block."""
    inside, states = False, []
    for line in lines:
        if FENCE_RE.match(line):
            states.append(True)
            inside = not inside
        else:
            states.append(inside)
    return states


def _chunks_by(lines: list[str], is_break, keep_break_line: bool) -> list[list[str]]:
    chunks: list[list[str]] = [[]]
    for line, in_code in zip(lines, _fence_states(lines)):
        if not in_code and is_break(line):
            chunks.append([line] if keep_break_line else [])
        else:
            chunks[-1].append(line)
    return chunks


def has_separators(text: str) -> bool:
    lines = text.splitlines()
    return any(SEPARATOR_RE.match(line) and not code for line, code in zip(lines, _fence_states(lines)))


def has_headings(text: str) -> bool:
    lines = text.splitlines()
    return any(HEADING_SPLIT_RE.match(line) and not code for line, code in zip(lines, _fence_states(lines)))


def resolve_mode(text: str, mode: str) -> str:
    if mode != "auto":
        return mode
    if has_separators(text):
        return "separator"
    if has_headings(text):
        return "heading"
    return "paragraph"


def make_title(text: str, limit: int = 48) -> str:
    for line in text.splitlines():
        if line.strip() and not FENCE_RE.match(line):
            title = INLINE_MARKUP_RE.sub("", LEADING_MARKUP_RE.sub("", line)).strip()
            return title if len(title) <= limit else title[: limit - 1].rstrip() + "…"
    return ""


def split_cards(text: str, mode: str = "auto") -> list[Card]:
    """Split ``text`` into non-empty cards.

    Modes: ``separator`` (a line with only ``---``), ``heading`` (before every
    ``#``/``##`` heading), ``paragraph`` (blank lines), ``none`` (one card) and
    ``auto`` (the first of separator → heading → paragraph that applies).
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    lines = text.split("\n")
    mode = resolve_mode(text, mode)

    if mode == "separator":
        chunks = _chunks_by(lines, SEPARATOR_RE.match, keep_break_line=False)
    elif mode == "heading":
        chunks = _chunks_by(lines, HEADING_SPLIT_RE.match, keep_break_line=True)
    elif mode == "paragraph":
        chunks = _chunks_by(lines, lambda line: not line.strip(), keep_break_line=False)
    else:
        chunks = [lines]

    cards = []
    for chunk in chunks:
        body = "\n".join(chunk).strip("\n")
        if body.strip():
            cards.append(Card(text=body, title=make_title(body)))
    return cards
