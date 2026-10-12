"""A deliberately small Markdown subset, parsed into styled spans.

The parser is UI-agnostic: it returns ``Line`` objects that the Tk view turns
into text-widget tags. Supported: ``#``/``##``/``###`` headings, bullet and
numbered lists (nested by indentation), ``- [ ]``/``- [x]`` checklists,
``>`` quotes, fenced code blocks, ``**bold**``, ``*italic*``, ```code```,
``==highlight==`` and ``~~strike~~``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

Span = tuple[str, frozenset]

INLINE_RE = re.compile(
    r"(\*\*|__)(?P<bold>.+?)\1"
    r"|`(?P<code>[^`]+)`"
    r"|==(?P<mark>.+?)=="
    r"|~~(?P<strike>.+?)~~"
    r"|\*(?!\s)(?P<italic>[^*]+?)(?<!\s)\*"
)
HEADING_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
CHECK_RE = re.compile(r"^(\s*)[-*+]\s+\[([ xX])\]\s+(.*)$")
BULLET_RE = re.compile(r"^(\s*)[-*+•]\s+(.*)$")
NUMBER_RE = re.compile(r"^(\s*)(\d+[.)])\s+(.*)$")
QUOTE_RE = re.compile(r"^\s*>\s?(.*)$")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
RULE_RE = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")


@dataclass
class Line:
    kind: str  # p, h1, h2, h3, bullet, number, check, quote, code, blank, rule
    spans: list[Span] = field(default_factory=list)
    marker: str = ""
    indent: int = 0
    done: bool = False

    @property
    def plain(self) -> str:
        return "".join(text for text, _ in self.spans)


def parse_inline(text: str, tags: frozenset = frozenset()) -> list[Span]:
    spans: list[Span] = []
    pos = 0
    for m in INLINE_RE.finditer(text):
        if m.start() > pos:
            spans.append((text[pos : m.start()], tags))
        if m.group("bold") is not None:
            spans += parse_inline(m.group("bold"), tags | {"bold"})
        elif m.group("code") is not None:
            spans.append((m.group("code"), tags | {"code"}))
        elif m.group("mark") is not None:
            spans += parse_inline(m.group("mark"), tags | {"mark"})
        elif m.group("strike") is not None:
            spans += parse_inline(m.group("strike"), tags | {"strike"})
        else:
            spans += parse_inline(m.group("italic"), tags | {"italic"})
        pos = m.end()
    if pos < len(text):
        spans.append((text[pos:], tags))
    return [s for s in spans if s[0]]


def _indent_level(spaces: str) -> int:
    return min(len(spaces.expandtabs(4)) // 2, 6)


def parse(text: str) -> list[Line]:
    lines: list[Line] = []
    in_code = False
    for raw in text.replace("\r\n", "\n").split("\n"):
        if FENCE_RE.match(raw):
            in_code = not in_code
            continue
        if in_code:
            lines.append(Line("code", [(raw or " ", frozenset({"code"}))]))
            continue
        if not raw.strip():
            if lines and lines[-1].kind != "blank":
                lines.append(Line("blank"))
            continue
        if m := HEADING_RE.match(raw):
            level = min(len(m.group(1)), 3)
            lines.append(Line(f"h{level}", parse_inline(m.group(2))))
        elif RULE_RE.match(raw):
            lines.append(Line("rule"))
        elif m := CHECK_RE.match(raw):
            done = m.group(2).lower() == "x"
            lines.append(Line("check", parse_inline(m.group(3)), "☑ " if done else "☐ ",
                              _indent_level(m.group(1)), done))
        elif m := BULLET_RE.match(raw):
            level = _indent_level(m.group(1))
            lines.append(Line("bullet", parse_inline(m.group(2)), "•◦▪"[level % 3] + " ", level))
        elif m := NUMBER_RE.match(raw):
            lines.append(Line("number", parse_inline(m.group(3)), m.group(2) + " ",
                              _indent_level(m.group(1))))
        elif m := QUOTE_RE.match(raw):
            lines.append(Line("quote", parse_inline(m.group(1))))
        else:
            lines.append(Line("p", parse_inline(raw.strip())))
    while lines and lines[-1].kind == "blank":
        lines.pop()
    return lines
