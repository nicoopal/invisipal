#!/usr/bin/env python3
"""Check an Invisipal guide: split it into cards exactly like the app does,
list them, and flag syntax Invisipal can't render or cards too dense to glance at.

Usage:
    python check_guide.py guide.md [--mode cue|script|any] [--json]

Exit code 1 if there are errors (unrenderable syntax, no cards), else 0.
Standard library only, Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# --- Splitting rules (mirror invisipal/cards.py) -----------------------------
SEPARATOR_RE = re.compile(r"^\s*-{3,}\s*$")
HEADING_SPLIT_RE = re.compile(r"^\s{0,3}#{1,2}\s+\S")
FENCE_RE = re.compile(r"^\s*(```|~~~)")
INLINE_MARKUP_RE = re.compile(r"(\*\*|__|==|~~|`|\*)")
LEADING_MARKUP_RE = re.compile(r"^\s*(#{1,6}\s+|>\s*|[-*+]\s+(\[[ xX]\]\s+)?|\d+[.)]\s+)")

# --- Lint rules ----------------------------------------------------------------
TABLE_RE = re.compile(r"^\s*\|.*\|\s*$")
LINK_RE = re.compile(r"!?\[[^\]]*\]\([^)]*\)")
HTML_RE = re.compile(r"<(/?[a-zA-Z][^>]*|!--.*?)>")
UNDERSCORE_ITALIC_RE = re.compile(r"(?<![\w_])_(?!_)[^_\s][^_]*?_(?![\w_])")
SETEXT_RE = re.compile(r"^\s*={3,}\s*$")
HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s+\S")
LIST_RE = re.compile(r"^\s*([-*+]|\d+[.)])\s+")
HIGHLIGHT_RE = re.compile(r"==(.+?)==")

BUDGETS = {  # mode: (max words, max list items)
    "cue": (45, 7),
    "script": (110, 99),
    "any": (130, 10),
}
TITLE_LIMIT = 48


def fence_states(lines):
    inside, states = False, []
    for line in lines:
        if FENCE_RE.match(line):
            states.append(True)
            inside = not inside
        else:
            states.append(inside)
    return states


def resolve_mode(lines, states):
    if any(SEPARATOR_RE.match(line) and not code for line, code in zip(lines, states)):
        return "separator"
    if any(HEADING_SPLIT_RE.match(line) and not code for line, code in zip(lines, states)):
        return "heading"
    return "paragraph"


def split_cards(text):
    """Return (split_mode, [(first_line_number, [lines])])."""
    text = text.replace("\r\n", "\n").replace("\r", "\n").replace("\t", "    ")
    lines = text.split("\n")
    states = fence_states(lines)
    mode = resolve_mode(lines, states)
    if mode == "separator":
        is_break, keep = SEPARATOR_RE.match, False
    elif mode == "heading":
        is_break, keep = HEADING_SPLIT_RE.match, True
    else:
        is_break, keep = (lambda line: not line.strip()), False

    chunks = [(1, [])]
    for number, (line, in_code) in enumerate(zip(lines, states), start=1):
        if not in_code and is_break(line):
            chunks.append((number if keep else number + 1, [line] if keep else []))
        else:
            chunks[-1][1].append(line)
    cards = []
    for start, chunk in chunks:
        while chunk and not chunk[0].strip():
            chunk, start = chunk[1:], start + 1
        while chunk and not chunk[-1].strip():
            chunk = chunk[:-1]
        if chunk:
            cards.append((start, chunk))
    return mode, cards


def make_title(lines):
    for line in lines:
        if line.strip() and not FENCE_RE.match(line):
            return INLINE_MARKUP_RE.sub("", LEADING_MARKUP_RE.sub("", line)).strip()
    return ""


def check(text, mode="cue"):
    max_words, max_items = BUDGETS[mode]
    split_mode, cards = split_cards(text)
    errors, warnings, report = [], [], []

    if not cards:
        errors.append("guide has no cards (it's empty)")
    if split_mode != "separator" and len(cards) > 1:
        warnings.append(f"no '---' separators: Invisipal splits by {split_mode}s. "
                        "Prefer explicit '---' lines between cards.")
    if len(cards) > 40:
        warnings.append(f"{len(cards)} cards is a lot to click through; consider merging or a backup section")

    for index, (start, lines) in enumerate(cards, start=1):
        states = fence_states(lines)
        prose = [line for line, code in zip(lines, states) if not code]
        title = make_title(lines)
        words = sum(len(re.findall(r"\S+", LEADING_MARKUP_RE.sub("", line))) for line in prose)
        items = sum(1 for line in prose if LIST_RE.match(line))
        highlights = sum(len(HIGHLIGHT_RE.findall(line)) for line in prose)
        where = f"card {index} (line {start})"

        first = next((line for line in lines if line.strip()), "")
        if not HEADING_RE.match(first):
            warnings.append(f"{where}: doesn't start with a heading; the 'next:' preview will show "
                            f"'{title[:30]}'")
        if len(title) > TITLE_LIMIT:
            warnings.append(f"{where}: title is {len(title)} chars, shown truncated in the preview")
        if words > max_words:
            warnings.append(f"{where}: {words} words (> {max_words} for '{mode}' cards)")
        if items > max_items:
            warnings.append(f"{where}: {items} list items (> {max_items} for '{mode}' cards)")
        if highlights > 2:
            warnings.append(f"{where}: {highlights} ==highlights==; keep 1-2 so they stand out")

        for offset, (line, in_code) in enumerate(zip(lines, states)):
            if in_code:
                continue
            at = f"line {start + offset}"
            if TABLE_RE.match(line):
                errors.append(f"{at}: table row (not rendered): {line.strip()[:60]}")
            if LINK_RE.search(line):
                errors.append(f"{at}: Markdown link/image (not rendered): {LINK_RE.search(line).group(0)[:60]}")
            if HTML_RE.search(line):
                errors.append(f"{at}: HTML tag/comment (not rendered): {HTML_RE.search(line).group(0)[:60]}")
            odd = [ch for ch in line if ord(ch) > 0xFFFF or ch == "️"]
            if odd:
                codes = " ".join(f"U+{ord(ch):04X}" for ch in odd)
                errors.append(f"{at}: emoji/symbol Invisipal can't render ({codes})")
            if SETEXT_RE.match(line):
                warnings.append(f"{at}: '===' underline headings aren't supported; use '## Title'")
            if UNDERSCORE_ITALIC_RE.search(line):
                warnings.append(f"{at}: _underscore italics_ aren't supported; use *asterisks*")

        report.append({"card": index, "line": start, "title": title, "words": words,
                       "list_items": items})

    return {"split_mode": split_mode, "cards": report, "errors": errors, "warnings": warnings}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("guide", type=Path)
    parser.add_argument("--mode", choices=sorted(BUDGETS), default="cue",
                        help="cue = glanceable bullets (default), script = read-aloud prose, any = lenient")
    parser.add_argument("--json", action="store_true", help="machine-readable output")
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):  # Windows consoles default to a legacy code page
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    text = args.guide.read_text(encoding="utf-8-sig")
    result = check(text, args.mode)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{args.guide.name}: {len(result['cards'])} cards (split by {result['split_mode']})\n")
        for card in result["cards"]:
            print(f"  {card['card']:>2}. {card['title'][:50]:<50} {card['words']:>4} words")
        for label, items in (("ERRORS", result["errors"]), ("Warnings", result["warnings"])):
            if items:
                print(f"\n{label}:")
                for item in items:
                    print(f"  - {item}")
        if not result["errors"] and not result["warnings"]:
            print("\nAll good.")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
