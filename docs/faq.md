# FAQ and troubleshooting

## The window shows up in my screen share

Work through this list:

1. **Look at the badge** in the window header.
   - `● private` (green): Windows reports the window as excluded from capture. Continue below.
   - `● blacked out` (amber): your Windows 10 is older than version 2004, so the window is shown as a black rectangle. Update Windows (run `winver` to check the version).
   - `● VISIBLE`: protection is off. Check that you did not start with `--no-protect` and that `"capture_protection"` is not `false` in `config.json`. If the badge is red, Windows refused the request; please [report it](../CONTRIBUTING.md#reporting-capture-issues).
2. **Make sure you are sharing the entire screen.** If you share a specific window, Invisipal is not part of it either way. If you share a *different monitor* than the one Invisipal is on, it is not captured because it is not on that screen.
3. **Test with a snip**: press `Win+Shift+S` and snip a rectangle over the window. If the snip shows the window, the problem is in Windows or the graphics driver, not in the meeting app.
4. **Update the meeting app** (Teams, Zoom, your browser for Meet) and your graphics driver. Capture code changes between versions.
5. **Is it a different kind of capture?** A phone filming the monitor, a capture card, a remote-desktop session or a virtual machine console are not covered. See [Limitations](../README.md#limitations-and-honest-caveats).
6. Still visible? Open an issue with your Windows build, the meeting app and its version, and what the badge said.

Always do the [phone test](../README.md#verify-its-invisible) before an important meeting.

## A hotkey doesn't work

- Press `?` in the window. Every hotkey is listed with the combination **actually in use**. A red entry marked `(in use by another app)` means another program already owns that combination; Windows allows only one owner.
- **Intel graphics**: some drivers use `Ctrl+Alt+Arrow` to rotate the screen. Disable the Intel hotkeys in the Intel graphics control panel, or rebind in `config.json`.
- **AltGr keyboards**: on Spanish / Latin American / German layouts, hotkeys like `Ctrl+Alt+Q` are automatically registered as `Ctrl+Alt+Shift+Q`. See below.
- Check the help view for `config error:` lines; a misspelled key name disables only that binding.
- Rebind the action in `config.json` while Invisipal is closed, then start it again:

  ```json
  { "hotkeys": { "next": "Ctrl+Shift+F8", "prev": "Ctrl+Shift+F7" } }
  ```
- Some games and remote-desktop clients capture the keyboard exclusively, so global hotkeys may not fire while they have focus.
- The hotkeys are read once at startup. After editing `config.json` restart Invisipal (`Ctrl+Alt+Q`, then launch again).

## Why is quit `Ctrl+Alt+Shift+Q` for me, and why can't I type `@`?

On keyboard layouts with an AltGr key, Windows reports AltGr as `Ctrl+Alt`. On Spanish or German layouts `AltGr+Q` types `@`. If Invisipal registered `Ctrl+Alt+Q` globally, it would grab that keystroke and `@` would stop working in every app.

So by default (`"avoid_altgr_conflicts": true`) Invisipal checks each `Ctrl+Alt+<key>` hotkey against your active layout and, if it would type a character, uses `Ctrl+Alt+Shift+<key>` instead. Only the affected hotkeys change; the help view shows what is active.

- If you can't type `@` or another AltGr character **and** Invisipal is running, make sure `avoid_altgr_conflicts` is `true` and restart Invisipal (the check runs at startup, so it doesn't notice later layout changes).
- If you prefer to keep `Ctrl+Alt+Q` and don't need `@` while it is running, set `"avoid_altgr_conflicts": false`.
- Or rebind to something without `Ctrl+Alt`, such as `Ctrl+Shift+F12`.

## The window disappeared or is off-screen

- Press `Ctrl+Alt+H` to toggle visibility. Launching Invisipal again also shows the running window.
- If it is running but positioned outside your monitors (after unplugging a display, for example), quit it (`Ctrl+Alt+Q`), open `config.json` and delete the `"x"` and `"y"` lines (or set them to `null`), then start it again. It will appear at the top-right of the primary screen. Invisipal already ignores a saved position that is not on any monitor, so this is rarely needed.
- If you don't see it in the taskbar or Alt+Tab, that's by design: set `"show_in_taskbar": true` if you want it listed (this makes it visible in the taskbar you share).
- If Click-through is on (the title says "click-through"), the window ignores the mouse. Press `Ctrl+Alt+T` to turn it off.
- The background can go down to 0% and the text to 20%. Press `Ctrl+Alt+PageUp` (background) or `Ctrl+Alt+Shift+Right` (text) a few times, or open the sliders with `◐`.

## The text is too big or too small

`Ctrl+Alt+Up` / `Ctrl+Alt+Down`, `+` / `-` with the window focused, or `Ctrl`+mouse wheel. The size is remembered (`font_size`, between 9 and 96). To change the font itself, set `font_family` in `config.json`. Window size is changed by dragging the `◢` grip at the bottom-right.

## Invisipal shows "config.json ignored"

The file is not valid JSON (a missing comma or quote, for example). Invisipal moves it aside to `config.broken.json`, starts with defaults and writes a fresh `config.json`. Fix the broken copy (a JSON validator helps) and rename it back while Invisipal is closed.

## Where are my guides and settings? How do I back them up?

In `Documents\Invisipal`: the `guides\` folder and `config.json`. Press `?` to see the exact paths. If your Documents folder is synced by OneDrive (the Windows default on many PCs), your guides are already backed up. Otherwise copy that folder to back it up or move it to another PC. To keep data somewhere else, use `--data-dir`, or create an empty `portable` file next to the app to keep everything next to it:

```powershell
pythonw invisipal.pyw --data-dir "D:\Notes\invisipal"
```

If you run from a clone in portable mode, personal guides in the repo's `guides/` folder are ignored by `.gitignore`, so they are never committed by accident.

## How do I delete or rename a guide?

Do it in the folder (the `Open folder` button in the library opens it in Windows Explorer; remember Explorer is a normal window and **is** captured if you share your screen). Invisipal doesn't delete files on its own.

## My edits in VS Code don't appear

Auto-reload checks once per second and is controlled by `"auto_reload"` (default `true`). It is paused while Invisipal's own editor is open. You can force it with `F5` (window focused) or `Ctrl+Alt+R`. Make sure you are editing the file in the guides folder and that it ends in `.md`, `.markdown` or `.txt`.

## One long card is cut off / how do I use it as a teleprompter?

Put the whole script in one card: either a guide with no `---` lines and no `#`/`##` headings that you split with `"split_mode": "none"`, or a single card among others (see the last card of `invisipal/examples/demo-meeting.md`). When a card is longer than the window, the status line shows `↓ more below` and "next" scrolls a page at a time, moving to the next card only at the end. Raise the text size to taste.

## Can I use it on macOS or Linux?

No. Invisipal depends on Windows-only APIs (`SetWindowDisplayAffinity`, `RegisterHotKey` and others), and the other platforms would need a different mechanism for each part. It isn't a simple port.

## It doesn't start

- Make sure Python is 3.10 or newer and includes tkinter: `python -c "import tkinter"`.
- Run `python -m invisipal` from a terminal to see error messages (`pythonw` hides them).
- If nothing appears, it may already be running: Invisipal allows only one instance, and a second launch just asks the first to show itself. Quit the first one from Task Manager if it is stuck.
- The `.exe` downloaded from the internet may trigger Windows SmartScreen or antivirus warnings because it is a freshly built, unsigned program. You can inspect and run the source with Python instead.

## Windows blocks Invisipal.exe: "An Application Control policy has blocked this file"

The full message is usually *"CreateProcess failed; code 4551. An Application Control policy has blocked this file."* It comes from **Smart App Control**, a Windows 11 feature that only lets apps run if Microsoft knows them or they carry a valid digital signature. Invisipal's releases are not code-signed yet, so it blocks them, and unlike SmartScreen there is no "Run anyway" button.

To check whether it's on: *Windows Security → App & browser control → Smart App Control*.

What you can do:

1. **Run from source (recommended).** Install Python 3.10+ from python.org, download or clone the repository, and double-click `invisipal.pyw`. Python is signed, so Smart App Control allows it, and the app is identical. For a Start menu entry, create a shortcut to `pythonw.exe` with the full path of `invisipal.pyw` as its argument, and pick `invisipal\assets\invisipal.ico` as its icon.
2. **Wait for a signed release.** Code signing is on the roadmap; signed builds pass Smart App Control.
3. **Turn Smart App Control off.** Not recommended just for this: it lowers your protection, and on many Windows versions it cannot be turned back on without resetting Windows.

If you installed with `Invisipal-Setup.exe`, uninstall it from *Settings → Apps* first.

## Does it send any data anywhere?

No. It has no network code, no telemetry and no dependencies. It reads and writes only `config.json` and your guides folder.

## Does it work with dual monitors?

Yes. The capture exclusion applies to the window wherever it is, so it is hidden whichever monitor you share. If you share only one monitor, you can also keep Invisipal on the other one, where it is not part of the share at all.
