# Contributing to Invisipal

Thanks for your interest. Bug reports, capture-compatibility reports and pull requests are all welcome.

## Development setup

You need Windows 10 (2004+) or Windows 11 and Python 3.10 or newer with tkinter (the python.org installer includes it).

```powershell
git clone https://github.com/nicoopal/invisipal.git
cd invisipal
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install pytest ruff
```

The app itself has no runtime dependencies; `pytest` and `ruff` are for development only (see `pyproject.toml` for the exact configuration).

### Run from source

```powershell
python -m invisipal                    # with a console, handy for tracebacks
pythonw invisipal.pyw                  # without a console, like end users
python -m invisipal --data-dir .\.dev  # throwaway data instead of Documents\Invisipal
python -m invisipal --no-protect       # window visible to capture, e.g. to take screenshots of it
```

Only one instance can run at a time. Quit the running one (`Ctrl+Alt+Q`) before starting another.

### Tests and lint

```powershell
python -m pytest
ruff check .
```

CI runs the same checks (`.github/workflows/ci.yml`). The pure-Python modules are testable on any OS, which is why all Win32 calls are isolated in `win32.py` and guarded by `IS_WINDOWS`.

### Standalone executable

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build.ps1
```

The result is written to `dist/`: `Invisipal-Setup.exe` (needs [Inno Setup 6](https://jrsoftware.org/isinfo.php), skipped with a warning otherwise; `installer/invisipal.iss`), `Invisipal-portable.exe` and `invisipal-cards.skill`. Releases are built by `.github/workflows/release.yml` when a `v*` tag is pushed.

The Microsoft Store package is built with `scripts/build-msix.ps1` (needs the Windows SDK and a prior `build.ps1`); its identity lives in `installer/msix/store-identity.json`. The `MSIX` workflow builds it, installs it with a throwaway test certificate, launches it and runs the Windows App Certification Kit. Store listing texts are in `docs/store-listing.md`; screenshots in `docs/store/`.

## Code layout

| Path | Responsibility |
|---|---|
| `invisipal.pyw` | Double-click launcher (no console window) |
| `invisipal/__main__.py` | CLI flags, data folder resolution, single-instance check, app start |
| `invisipal/app.py` | The Tk window: header, reader / editor / library / help views, local keys, timer, watchdog, auto-reload |
| `skills/invisipal-cards/` | Claude skill that writes guides; `scripts/check_guide.py` must split cards exactly like `cards.py` (enforced by `tests/test_skill_checker.py`) |
| `invisipal/paths.py` | Data folder: `Documents\Invisipal` by default, `portable` marker, first-run seeding |
| `invisipal/win32.py` | All `ctypes` Win32 calls: display affinity, extended styles, single-instance event, AltGr probe, DPI |
| `invisipal/hotkeys.py` | Hotkey parsing, AltGr conflict resolution, the `RegisterHotKey` message-loop thread |
| `invisipal/cards.py` | Splitting a guide into cards (separator / heading / paragraph / none) |
| `invisipal/markdown.py` | The small Markdown subset, parsed into UI-agnostic styled spans |
| `invisipal/guides.py` | The guides folder: list, read, atomic write, unique names |
| `invisipal/config.py` | Defaults, validation and atomic persistence of `config.json` |
| `tests/` | pytest suite |
| `scripts/build.ps1` | Builds the standalone `.exe` |
| `docs/` | Technical write-up and FAQ |

## Guidelines

- **Standard library only.** No third-party runtime dependencies. This keeps the app auditable and the `.exe` small.
- **No popups, extra top-level windows or native dialogs.** Anything that opens a separate window (message boxes, file pickers, `Toplevel`, menus, tooltips as windows) is a window that is not protected from capture and could leak into a screen share. New UI belongs inside the existing window as another view or an overlay widget. If a feature unavoidably needs a second window, it must apply the same capture exclusion and be discussed in an issue first.
- **Keep Win32 calls in `win32.py`.** Other modules should call small, documented helpers there. Declare `argtypes` and `restype` for every function you add, and keep the module importable on non-Windows platforms.
- **Never show the window before protection is applied.** The window starts at alpha 0 and is revealed after `SetWindowDisplayAffinity` succeeds.
- **Keep parsing code UI-free** (`cards.py`, `markdown.py`, `config.py`, `guides.py`) and covered by tests.
- **Write config and guides atomically** (write a temp file, then `os.replace`) so a crash never corrupts a user's notes.
- Add a test for new behavior, run `ruff`, and add a line to `CHANGELOG.md` under `[Unreleased]`.
- Keep the Markdown subset small on purpose. Cards are glanced at, not studied.

## Pull requests

1. Open an issue first for anything larger than a small fix, so we can agree on the approach.
2. Keep each PR focused on one change.
3. Make sure `pytest` and `ruff` pass.
4. Describe what you changed and how you tested it. For UI changes, include a screenshot taken with `--no-protect`.

## Reporting capture issues

The most valuable bug report is "Invisipal was visible to the audience". Please open an issue and include:

- The **Windows version and build** (run `winver`, for example "Windows 11 25H2, build 26200.xxxx").
- The **meeting or capture app and its version** (Teams, Zoom, Meet in which browser, OBS, ...), and whether you shared the **entire screen** or a window.
- What the **badge** in the Invisipal header said (`private`, `blacked out`, `VISIBLE`).
- Whether a `Win+Shift+S` snip over the window shows it.
- How you observed it (second device, recording, a participant telling you).
- Your GPU and driver version, and whether you use multiple monitors, Remote Desktop or a virtual machine.

Please do not include screenshots that contain private information.

## Reporting other bugs

Include your Windows version, how you run Invisipal (source or `.exe`, and the version from `--version`), what you did, what you expected and what happened. The help view (`?`) shows hotkey status and file locations and is useful to paste into the report. Remove anything private from your `config.json` first.
