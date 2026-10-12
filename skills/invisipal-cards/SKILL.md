---
name: invisipal-cards
description: Turns any text (messy notes, a speech, an email thread, a doc, bullet dumps) into a ready-to-use Invisipal guide, a .md file of glanceable cards separated by --- that the Invisipal app shows one at a time, hidden from screen sharing. Interviews the user first about the meeting, the format they want (quick cue cards, a full teleprompter script, a checklist, Q&A/objection banks) and the language, then writes, checks and saves the guide. Use this skill whenever the user mentions Invisipal, cue cards, speaker notes, talking points, a teleprompter, a "walltext", "tarjetas", "guía para la reunión", or wants notes in front of them during a Teams/Zoom/Meet call, a demo, a pitch, an interview or a presentation, even if they don't name Invisipal.
---

# Invisipal cards

Invisipal is a Windows app that shows notes in a small translucent window that stays invisible when the user shares their screen. A **guide** is a plain `.md` or `.txt` file; a line containing only `---` starts a new **card**, and the app shows one card at a time with a counter ("3 / 10") and a preview of the next card's title. The user advances with `Ctrl+Alt+→` while talking, so every card must be readable in a glance, mid-sentence, with people watching.

Your job: find out what the user actually needs in front of their eyes during that meeting, then turn their material into cards that serve that moment. Content that is perfect on paper but too dense to read while speaking is a failure here.

Read `references/format.md` before writing your first guide. It is the exact syntax Invisipal renders (a small Markdown subset) and what breaks. For card patterns by meeting type (sales call, talk, interview, 1:1, negotiation, class...), skim `references/patterns.md`.

## 1. Interview first, briefly

Ask before writing, because the right cards depend on things the text alone doesn't reveal. A pitch someone knows by heart needs five keyword cards; the same pitch for a nervous first-timer needs a near-full script. Keep it to one round of at most 4 to 5 questions, and skip anything the user already told you. If an `AskUserQuestion`-style tool is available, use it with concrete options; otherwise ask in plain text as a short numbered list with defaults in parentheses, so the user can answer "1b, 2 default, 3 Spanish".

What to find out, in priority order:

1. **The moment**: what kind of meeting, who's on the other side, how long, and what a good outcome looks like. One sentence from the user is enough.
2. **Format**: offer these, with a recommendation based on what you know:
   - **Cue cards**: a heading plus 3 to 6 short bullets or keywords. For people who know the material and want reminders. The default for most meetings.
   - **Teleprompter script**: full sentences to read aloud, split into short paragraphs. For speeches, recorded videos, openings and closings, or non-native-language presentations.
   - **Hybrid**: a scripted opening and closing with cue cards in between. Often the best choice for presentations and pitches.
   - **Checklist / reference**: checkboxes, numbers, names, prices and answers to likely questions. For calls where they mostly listen and need facts on demand.
3. **Language and voice**: the language to write in (default: the user's language, or the source's if they differ, and ask when they differ), first person or not, formal or casual.
4. **Size**: roughly how many cards, or how long the talk is. Default: one card per topic or minute, about 6 to 12 cards. Also ask whether they keep the window small (fewer words per card) or large.
5. **Extras worth offering**: a backup card bank at the end (objections, tough questions, key numbers), minute markers in titles ("Demo (5 min)"), and `==highlights==` for the one thing they must not forget.

If the user says "just do it", or the request already answers these, skip the interview, state your assumptions in one line, and write. You can always refine afterwards.

## 2. Shape the content for glancing

Readers of these cards are mid-conversation and looking away from the camera for a second at a time. That drives everything:

- **Start every card with a short `##` heading.** The app uses a card's first line as its title in the "next: ..." preview, so a good heading tells the user what's coming before they press the key. Add timing when the user wants pacing: `## Demo (5 min)`.
- **One idea per card.** If a card covers two things, split it. Cards are cheap, and the counter shows progress.
- **Respect the glance budget.** Cue cards: at most about 40 words and 6 bullets, mostly fragments, not sentences. Script cards: about 60 to 90 words, one or two short paragraphs, written for the ear (short sentences, natural rhythm, no parentheses or citations). A longer card still works, because "next" pages down before advancing, but it reads worse. Checklist cards: up to about 8 items.
- **Make the key thing pop.** Use `**bold**` for the words the user must say, `==highlight==` for one critical fact or ask per card at most (if everything is highlighted, nothing is), and `- [ ]` for things to do or confirm during the call.
- **Keep the user's facts exactly.** Numbers, names, prices and dates come from the source verbatim. Never invent figures, quotes or claims to fill a card. If something is missing, put a visible placeholder like `[price?]` and mention it when you deliver.
- **Order cards by when they're needed** in the meeting, not by where the material appeared in the source. Reference-only material (objections, FAQs, numbers) goes in clearly titled cards at the end.
- **Speak the user's language and register.** A Spanish speaker in Argentina gets "vos", a Spanish speaker in Spain "tú", unless they say otherwise. Match the formality of the meeting.

Typical skeleton for a meeting (adapt it; don't force it):

```markdown
## Opening (1 min)
- Thank them for the time
- **Goal today:** decide on the pilot
- Agenda: context · demo · next steps

---

## Their situation
- Ask: what's the #1 problem this quarter?
- Who else is involved in the decision?

---
...
---

## Backup: objections
**"Too expensive"** → compare with the cost of doing nothing
**"Not now"** → what would need to change? Agree on a date
```

## 3. Check it

If you can run Python, run the bundled checker on the file:

```bash
python <this-skill-dir>/scripts/check_guide.py path/to/guide.md --mode cue
```

Use `--mode script` for teleprompter guides. It splits the guide exactly like Invisipal does, lists every card with its title and word count, and flags syntax the app can't render (tables, links, images, emoji, HTML) and cards over the glance budget. Fix errors; treat warnings as judgment calls, since a deliberately long closing script is fine. If you can't run code, check the rules in `references/format.md` by eye.

## 4. Deliver

- **Save the guide as a file** named after the meeting in kebab-case with a `.md` extension, e.g. `pitch-acme-logistica.md`. If you have filesystem access on the user's Windows PC, save it straight into Invisipal's guides folder, normally `%USERPROFILE%\Documents\Invisipal\guides\` (the Documents folder may be redirected, e.g. `%USERPROFILE%\OneDrive\Documents\Invisipal\guides\`, or localized, e.g. `...\Documentos\...`, so look for an existing `Invisipal\guides` folder first). Invisipal picks it up in its library (`L`). Otherwise create the file wherever deliverables go in your environment.
- **Also give the guide in a single fenced code block** when the user may want to copy it. In Invisipal, copying the text and pressing `Ctrl+V` in the window creates a new guide from the clipboard, so a copy-paste is a complete workflow.
- **Close with a short summary**: number of cards, the format you chose, any `[placeholders]` the user must fill in, and one tip relevant to their meeting (for example "use `Ctrl+Alt+↑` to enlarge the text for the script cards").

Then offer one round of tweaks: shorter, more scripted, a different order, or another language.

## Notes

- If the material is huge (a 20-page doc), don't transcribe it. Ask what part they'll actually talk about, or propose a selection, and keep the rest as a short reference card or out entirely.
- If the user wants several meetings, make one guide file per meeting. Invisipal switches guides with `Ctrl+Alt+G`.
- Invisipal is for the user's own notes. If they make clear the setting forbids notes or aids (an exam, a proctored test, an interview with an explicit no-notes rule), say so briefly and let them decide; don't lecture otherwise. Preparing talking points for interviews, sales calls and presentations is ordinary, legitimate use.
