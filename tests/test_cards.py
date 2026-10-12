from __future__ import annotations

import pytest

from invisipal.cards import make_title, resolve_mode, split_cards


def texts(cards):
    return [c.text for c in cards]


class TestSeparatorMode:
    def test_splits_on_dashes_lines(self):
        cards = split_cards("one\n---\ntwo\n----\nthree", "separator")
        assert texts(cards) == ["one", "two", "three"]

    def test_separator_with_surrounding_spaces(self):
        assert texts(split_cards("a\n  ---  \nb", "separator")) == ["a", "b"]

    def test_two_dashes_is_not_a_separator(self):
        assert texts(split_cards("a\n--\nb", "separator")) == ["a\n--\nb"]

    def test_dashes_inside_text_do_not_split(self):
        assert len(split_cards("a --- b\nc", "separator")) == 1

    def test_separator_inside_fenced_code_does_not_split(self):
        text = "intro\n```\nx\n---\ny\n```\n---\nnext"
        cards = split_cards(text, "separator")
        assert len(cards) == 2
        assert "x\n---\ny" in cards[0].text
        assert cards[1].text == "next"

    def test_separator_inside_tilde_fence_does_not_split(self):
        cards = split_cards("~~~\n---\n~~~", "separator")
        assert len(cards) == 1

    def test_empty_cards_dropped(self):
        assert texts(split_cards("---\n\n---\nreal\n---\n   \n---", "separator")) == ["real"]


class TestHeadingMode:
    def test_splits_before_h1_and_h2(self):
        cards = split_cards("# A\nx\n## B\ny", "heading")
        assert texts(cards) == ["# A\nx", "## B\ny"]

    def test_preamble_is_its_own_card(self):
        cards = split_cards("intro\n\n# A\nx", "heading")
        assert texts(cards) == ["intro", "# A\nx"]

    def test_h3_does_not_split(self):
        cards = split_cards("# A\n### sub\nx", "heading")
        assert len(cards) == 1

    def test_hash_without_space_is_not_heading(self):
        assert len(split_cards("#tag\n#other", "heading")) == 1

    def test_heading_inside_code_fence_does_not_split(self):
        text = "# A\n```\n# comment\n```\n# B"
        assert len(split_cards(text, "heading")) == 2

    def test_title_from_heading(self):
        cards = split_cards("# Intro\nbody\n## Next\nmore", "heading")
        assert [c.title for c in cards] == ["Intro", "Next"]


class TestParagraphMode:
    def test_splits_on_blank_lines(self):
        cards = split_cards("a\nb\n\nc\n\n\n\nd", "paragraph")
        assert texts(cards) == ["a\nb", "c", "d"]

    def test_whitespace_only_line_counts_as_blank(self):
        assert texts(split_cards("a\n   \nb", "paragraph")) == ["a", "b"]


class TestNoneMode:
    def test_single_card(self):
        cards = split_cards("a\n---\nb\n\n# c", "none")
        assert len(cards) == 1
        assert "---" in cards[0].text

    def test_blank_text_yields_no_cards(self):
        assert split_cards("  \n\n \n", "none") == []


class TestAuto:
    def test_separator_wins_over_heading(self):
        text = "# A\nx\n---\n# B\ny"
        assert resolve_mode(text, "auto") == "separator"
        assert len(split_cards(text)) == 2

    def test_heading_wins_over_paragraph(self):
        text = "# A\nx\n\ny\n## B"
        assert resolve_mode(text, "auto") == "heading"

    def test_falls_back_to_paragraph(self):
        assert resolve_mode("a\n\nb", "auto") == "paragraph"

    def test_separator_only_in_code_is_ignored(self):
        text = "```\n---\n```\n# H"
        assert resolve_mode(text, "auto") == "heading"

    def test_heading_only_in_code_is_ignored(self):
        text = "```\n# not a heading\n```"
        assert resolve_mode(text, "auto") == "paragraph"

    @pytest.mark.parametrize("mode", ["separator", "heading", "paragraph", "none"])
    def test_explicit_mode_passes_through(self, mode):
        assert resolve_mode("anything", mode) == mode

    def test_unknown_mode_behaves_like_none(self):
        assert len(split_cards("a\n\nb", "bogus")) == 1


class TestNormalisation:
    def test_crlf_input(self):
        cards = split_cards("one\r\n---\r\ntwo\r\n", "separator")
        assert texts(cards) == ["one", "two"]
        assert all("\r" not in c.text for c in cards)

    def test_lone_cr_input(self):
        assert texts(split_cards("one\r---\rtwo", "separator")) == ["one", "two"]

    def test_tabs_become_spaces(self):
        assert split_cards("\t- item", "none")[0].text == "    - item"

    def test_empty_input(self):
        assert split_cards("") == []


class TestMakeTitle:
    @pytest.mark.parametrize(
        "text, expected",
        [
            ("# Heading", "Heading"),
            ("### Deep heading", "Deep heading"),
            ("- bullet item", "bullet item"),
            ("* star item", "star item"),
            ("- [ ] todo", "todo"),
            ("- [x] done", "done"),
            ("1. numbered", "numbered"),
            ("2) numbered paren", "numbered paren"),
            ("> quote", "quote"),
            ("**bold** and *it* and `code`", "bold and it and code"),
            ("==hi== ~~gone~~", "hi gone"),
            ("plain", "plain"),
        ],
    )
    def test_strips_markers(self, text, expected):
        assert make_title(text) == expected

    def test_skips_leading_blank_and_fence_lines(self):
        assert make_title("\n  \n```\ncode line") == "code line"

    def test_empty(self):
        assert make_title("") == ""
        assert make_title("   \n  ") == ""

    def test_truncation(self):
        title = make_title("x" * 100, limit=10)
        assert title == "x" * 9 + "…"
        assert len(title) == 10

    def test_exact_limit_not_truncated(self):
        assert make_title("y" * 48) == "y" * 48

    def test_default_limit_is_48(self):
        assert len(make_title("z" * 200)) == 48
