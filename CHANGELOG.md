# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Microsoft Store packaging: MSIX manifest and assets (`installer/msix/`), `scripts/build-msix.ps1`, an `MSIX` workflow that installs and launches the package and runs the App Certification Kit, a privacy policy (`PRIVACY.md`) and the Store listing texts (`docs/store-listing.md`).

## [1.2.0] - 2026-10-12

### Added

- **`Invisipal.zip`**, the recommended download: the Python version plus `Install Invisipal.pyw`, a small setup window (English/Spanish) that copies the app to `%LOCALAPPDATA%\Invisipal\app` and creates Start menu, desktop and optional startup shortcuts that run it with `pythonw.exe`. It updates and uninstalls too. Because Python is signed, it works on PCs where Smart App Control blocks the unsigned executables.

### Fixed

- Card index: titles were hard to click and the mouse wheel didn't scroll the list. The index used the transparent key color as its background, so clicks and the wheel fell through to the window behind; it now has its own sidebar background, taller rows and a full-width hover highlight.
- The "hotkey in use by another app" message no longer lists every hotkey on one line.

### Documentation

- Smart App Control (Windows 11) blocks the unsigned executables with "An Application Control policy has blocked this file" (code 4551). Documented the cause and the workarounds in the README and FAQ.

## [1.1.0] - 2026-10-12

### Added (window)

- Separate **background** and **text** opacity: the window is now two capture-excluded layers (a translucent backdrop plus a color-keyed text layer). Inline sliders (`◐` / `A`), hotkeys (`Ctrl+Alt+PageUp/PageDown`, `Ctrl+Alt+Shift+Right/Left`) and `Alt`/`Alt+Shift` + wheel. The old `opacity` setting and `opacity_up/down` hotkeys are migrated.
- **Card index** sidebar: click to jump, drag to resize, `Ctrl` + wheel for its text size, hide with `◧`, `I` or `Ctrl+Alt+I`.
- **Snap positions**: `Ctrl+Alt+Shift+Home/PageUp/End/PageDown` for the four corners and `Ctrl+Alt+Shift+Up/Down` for top/bottom center, inside the monitor's work area.
- Drag the see-through background to move the window.

### Added

- `invisipal-cards` Claude skill (`skills/invisipal-cards/`): interviews the user, turns any text into an Invisipal guide (cue cards, teleprompter script, hybrid or checklist), checks it with a bundled validator that mirrors the app's card splitting, and saves it to the guides folder. Released as `invisipal-cards.skill`.

### Added (packaging)

- App icon (an eye with a prohibition sign), also shown in the window header.
- Per-user installer `Invisipal-Setup.exe` (Inno Setup: Start menu, optional desktop and startup shortcuts, uninstaller, refuses to run while Invisipal is open) and a single-file `Invisipal-portable.exe`, both with fixed names so `releases/latest/download/` links always work. The release zip is gone.

### Changed

- Example guides moved into the package (`invisipal/examples/`) so every build seeds them.
- Settings and guides now live in `Documents\Invisipal` (OneDrive-redirected Documents supported), seeded with the example guides on first run; an older `config.json` next to the app is copied over. An empty `portable` file next to the app keeps data next to the app instead.

## [1.0.0] - 2026-10-12

Initial release.

### Added

- Translucent, dark, borderless, always-on-top window that shows notes one card at a time, with a card counter, progress bar and a preview of the next card.
- Exclusion from screen capture through `SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE)`, so the window is not shared when the entire screen is shared in Teams, Zoom, Google Meet, OBS or screenshots. Falls back to `WDA_MONITOR` (black box) on Windows 10 builds before 2004.
- Header status badge: `private`, `blacked out` or `VISIBLE`.
- The window starts fully transparent and becomes visible only after capture protection is applied; a watchdog re-applies it every second.
- Fourteen global hotkeys registered from a dedicated message-loop thread: next / previous card, first / last, text size, opacity, show / hide, reload, quit, click-through, next guide and timer. All rebindable in `config.json`; an empty string disables a hotkey.
- AltGr conflict handling: `Ctrl+Alt+<key>` hotkeys that would type a character on the active keyboard layout (for example `@` on Spanish or German layouts) are registered as `Ctrl+Alt+Shift+<key>` instead (`avoid_altgr_conflicts`).
- Teleprompter paging: the "next" action scrolls through a long card before advancing.
- Show / hide without stealing focus from the meeting app.
- Click-through mode (`WS_EX_TRANSPARENT`).
- Hidden from the taskbar and Alt+Tab by default (`show_in_taskbar`).
- Single-instance behavior: launching again shows the running window.
- Guides as plain `.md`, `.markdown` and `.txt` files with automatic reload when edited externally.
- Card splitting modes: `auto`, `separator` (`---`), `heading`, `paragraph` and `none`.
- Markdown subset: headings, bullet / numbered / nested lists, checklists, quotes, fenced code, bold, italic, inline code, `==highlight==` and `~~strikethrough~~`.
- In-window editor, guide library and help view (no popups or extra windows, which would be capturable); paste the clipboard as a new guide with `Ctrl+V`.
- Meeting timer (start / pause, double-click to reset).
- Remembered window position, size, opacity, text size and card position per guide, stored in `config.json`.
- Customizable theme colors.
- Command-line flags `--data-dir`, `--guide`, `--no-protect` and `--version`.
- Example guides in Spanish (`invisipal/examples/guia.txt`) and English (`invisipal/examples/demo-meeting.md`).
- Pure Python standard library implementation (tkinter + ctypes) with no dependencies; buildable as a standalone `.exe` with `scripts/build.ps1`.

[Unreleased]: https://github.com/nicoopal/invisipal/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/nicoopal/invisipal/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/nicoopal/invisipal/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/nicoopal/invisipal/releases/tag/v1.0.0
