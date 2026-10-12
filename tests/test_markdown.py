from __future__ import annotations

import pytest

from invisipal.markdown import parse, parse_inline


def kinds(text):
    return [line.kind for line in parse(text)]


def span_map(text):
    return [(t, set(tags)) for t, tags in parse_inline(text)]


class TestBlocks:
    @pytest.mark.parametrize(
        "hashes, kind",
        [("#", "h1"), ("##", "h2"), ("###", "h3"), ("####", "h3"), ("######", "h3")],
    )
    def test_headings_clamp_to_h3(self, hashes, kind):
        (line,) = parse(f"{hashes} Title")
        assert line.kind == kind
        assert line.plain == "Title"

    def test_heading_trailing_hashes_removed(self):
        assert parse("## Title ##")[0].plain == "Title"

    def test_seven_hashes_is_paragraph(self):
        assert parse("####### x")[0].kind == "p"

    def test_hash_without_space_is_paragraph(self):
        assert parse("#tag")[0].kind == "p"

    def test_bullets_and_markers(self):
        lines = parse("- a\n* b\n+ c\n• d")
        assert [ln.kind for ln in lines] == ["bullet"] * 4
        assert all(ln.marker == "• " for ln in lines)
        assert [ln.plain for ln in lines] == ["a", "b", "c", "d"]

    def test_bullet_nesting_levels_and_markers(self):
        lines = parse("- a\n  - b\n    - c\n      - d")
        assert [ln.indent for ln in lines] == [0, 1, 2, 3]
        assert [ln.marker for ln in lines] == ["• ", "◦ ", "▪ ", "• "]

    def test_tab_indent_counts_as_four_spaces(self):
        assert parse("\t- a")[0].indent == 2

    def test_indent_is_capped(self):
        assert parse(" " * 100 + "- deep")[0].indent == 6

    def test_numbered_list(self):
        lines = parse("1. one\n2) two\n  10. ten")
        assert [ln.kind for ln in lines] == ["number"] * 3
        assert [ln.marker for ln in lines] == ["1. ", "2) ", "10. "]
        assert lines[2].indent == 1
        assert lines[0].plain == "one"

    def test_checkboxes(self):
        todo, done, upper = parse("- [ ] todo\n- [x] done\n* [X] DONE")
        assert (todo.kind, todo.done, todo.marker) == ("check", False, "☐ ")
        assert (done.kind, done.done, done.marker) == ("check", True, "☑ ")
        assert upper.done is True
        assert todo.plain == "todo"

    def test_quote(self):
        lines = parse("> quoted **bold**\n>no space")
        assert [ln.kind for ln in lines] == ["quote", "quote"]
        assert lines[0].plain == "quoted bold"
        assert lines[1].plain == "no space"

    def test_fenced_code(self):
        lines = parse("```python\n# not heading\n- not bullet\n\nx = **1**\n```\nafter")
        assert [ln.kind for ln in lines] == ["code", "code", "code", "code", "p"]
        assert lines[0].plain == "# not heading"
        assert lines[2].plain == " "  # empty code line keeps a space so it has height
        assert lines[3].plain == "x = **1**"
        assert lines[0].spans[0][1] == frozenset({"code"})

    def test_tilde_fence(self):
        assert kinds("~~~\na\n~~~") == ["code"]

    def test_unclosed_fence_swallows_rest(self):
        assert kinds("```\na\nb") == ["code", "code"]

    @pytest.mark.parametrize("rule", ["***", "* * *", "___", "_ _ _", "  ***  "])
    def test_horizontal_rules(self, rule):
        assert kinds(rule) == ["rule"]

    def test_paragraph(self):
        (line,) = parse("  hello **world**  ")
        assert line.kind == "p"
        assert line.plain == "hello world"

    def test_blank_lines_collapse_and_trailing_removed(self):
        assert kinds("a\n\n\n\nb\n\n\n") == ["p", "blank", "p"]

    def test_only_blank(self):
        assert parse("\n \n\t\n") == []

    def test_crlf(self):
        assert kinds("# a\r\n- b\r\n") == ["h1", "bullet"]
        assert parse("x\r\n")[0].plain == "x"

    def test_empty(self):
        assert parse("") == []


class TestInline:
    def test_plain(self):
        assert span_map("hello") == [("hello", set())]

    def test_empty(self):
        assert parse_inline("") == []

    @pytest.mark.parametrize(
        "text, tag",
        [("**b**", "bold"), ("__b__", "bold"), ("*b*", "italic"), ("`b`", "code"),
         ("==b==", "mark"), ("~~b~~", "strike")],
    )
    def test_single_style(self, text, tag):
        assert span_map(text) == [("b", {tag})]

    def test_mixed_line_preserves_order_and_text(self):
        spans = span_map("a **b** c *d* e")
        assert [t for t, _ in spans] == ["a ", "b", " c ", "d", " e"]
        assert [tags for _, tags in spans] == [set(), {"bold"}, set(), {"italic"}, set()]

    def test_bold_inside_highlight(self):
        assert span_map("==very **important** note==") == [
            ("very ", {"mark"}),
            ("important", {"mark", "bold"}),
            (" note", {"mark"}),
        ]

    def test_italic_inside_bold(self):
        assert span_map("**a *b* c**") == [
            ("a ", {"bold"}), ("b", {"bold", "italic"}), (" c", {"bold"}),
        ]

    def test_strike_inside_highlight(self):
        assert span_map("==x ~~y~~==") == [("x ", {"mark"}), ("y", {"mark", "strike"})]

    def test_code_is_not_parsed_further(self):
        assert span_map("`**not bold** and *it*`") == [("**not bold** and *it*", {"code"})]

    def test_code_inside_bold(self):
        assert span_map("**run `ls`**") == [("run ", {"bold"}), ("ls", {"bold", "code"})]

    def test_unbalanced_markers_are_literal(self):
        assert span_map("a ** b") == [("a ** b", set())]
        assert span_map("`open") == [("`open", set())]

    def test_star_followed_by_space_is_not_italic(self):
        assert span_map("2 * 3 * 4") == [("2 * 3 * 4", set())]

    def test_inherited_tags(self):
        assert parse_inline("x", frozenset({"bold"})) == [("x", frozenset({"bold"}))]

    def test_no_empty_spans(self):
        assert all(text for text, _ in parse_inline("**a****b**"))
