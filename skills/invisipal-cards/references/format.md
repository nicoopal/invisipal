# Invisipal guide format

This is exactly what Invisipal (v1.x) renders. Anything outside this subset shows up as literal characters, which looks broken on a card the user is reading live.

## Files

- Plain UTF-8 text with a `.md`, `.markdown` or `.txt` extension. Prefer `.md`.
- One file per meeting. The file name (without extension) is shown as the guide name in the app header, so keep it short and readable: `pitch-acme.md`, `standup-lunes.md`.

## How a guide becomes cards

Invisipal picks the first rule that applies (its "auto" split mode):

1. **Separator**: if any line contains only `---` (three or more dashes, optional surrounding spaces), every such line starts a new card. **Always use this.** It's explicit and predictable.
2. **Heading**: otherwise, a new card starts before every `#` or `##` heading.
3. **Paragraph**: otherwise, every blank-line-separated paragraph is its own card.

Details:

- Leave a blank line before and after each `---`. It isn't required, but it keeps the file readable when the user edits it.
- `---` inside a fenced code block does not split.
- Empty cards are dropped, so a leading or trailing `---` is harmless.
- A card's **title** (used in the footer's "next: ..." preview) is its first non-empty line with Markdown markers stripped, cut to about 48 characters. That's why every card should start with a short `##` heading.

## Supported formatting

| Write | Renders as |
|---|---|
| `# Title` | Large heading (use for the first card or a section opener only) |
| `## Title` | Card heading. Use this on every card |
| `### Title` | Small heading |
| `#### ...` and deeper | Rendered as `###` |
| `- item`, `* item`, `+ item` | Bullet. Indent 2 spaces per level for nesting (•, ◦, ▪) |
| `1. item` or `1) item` | Numbered item; the number is kept as written |
| `- [ ] task` / `- [x] done` | ☐ / ☑ checkbox. Done items are dimmed and struck through. Display only, not clickable |
| `> text` | Quote with an accent bar (good for verbatim lines to read or quote) |
| `**bold**` or `__bold__` | Bold |
| `*italic*` | Italic (`_italic_` is NOT supported, so underscores stay literal) |
| `` `code` `` | Monospace with a dark background (good for shortcuts and IDs) |
| `==highlight==` | Yellow highlight: the one thing not to forget |
| `~~strike~~` | Strikethrough |
| fenced code block with three backticks | Monospace block |
| `***` or `___` (or `- - -`) on its own line | A small centered divider inside a card |
| blank line | Paragraph gap (several blank lines collapse into one) |

Inline styles can nest (`==**must say**==`), except inside `` `code` ``.

## Not supported (avoid)

- **Tables** (`| a | b |`): shown as raw pipes. Use bullets like `**Plan A**: $10/mo · 3 seats`.
- **Links and images** (`[text](url)`, `![]()`): shown raw. Write the URL plainly if it's needed at all.
- **Emoji and other symbols outside the basic plane**: Tk can't render color emoji and they can distort the line height. Use plain arrows and symbols that render fine: → ← ↑ ↓ • · ✓ ✗ ★ ⚠ ☐.
- **HTML tags and comments**: shown raw.
- **Footnotes, definition lists, setext headings** (`Title` underlined with `===`): shown raw. Note that a `---` line under text is a card separator here, not a heading underline.
- `_underscore italics_`: shown raw.

## How much fits

The default window is about 620 × 440 px with 20 pt Segoe UI, which shows roughly **8 to 10 lines of about 45 characters**, i.e. 60 to 80 words of prose, or a heading and 5 to 6 short bullets. Users resize the window and change the text size (`Ctrl+Alt+↑/↓`), so this is a guide, not a hard limit. When a card is taller than the window, the footer shows "↓ more below" and `Ctrl+Alt+→` scrolls a page before moving to the next card, so long script cards still work.

## Example guide

```markdown
# Pitch: Acme Logistics

Goal: ==agree on a 30-day pilot==

---

## Opening (1 min)

- Thanks for the time, **Laura** and team
- 30 min: their context → demo → next steps
- Ask: anyone else joining?

---

## Discovery

- What's the #1 bottleneck in dispatch today?
- How do they track late deliveries now?
- Who signs off on new tools?

---

## Demo flow

- [ ] Live map with today's routes
- [ ] Auto-reassign when a truck is late
- [ ] Weekly report → **saves ~6 h/week**

---

## Pricing

- Pilot: **free, 30 days**, up to 20 trucks
- Then `$12 / truck / month`, annual
- ==Never discount on the first call==

---

## Close

> "If the pilot shows the 6 hours, can we roll it out in Q1?"

- Agree on start date and owner
- Book the review call **before** hanging up
```
