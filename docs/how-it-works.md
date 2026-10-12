# How Invisipal works

This document explains the mechanisms behind Invisipal and the reasoning for some non-obvious choices. For usage, see the [README](../README.md).

## Display affinity

Windows lets a window declare how it should appear in screen capture with `SetWindowDisplayAffinity(hwnd, affinity)`:

| Value | Constant | Available since | Effect in captures |
|---|---|---|---|
| `0x00` | `WDA_NONE` | Windows 7 | Normal. The window is captured. |
| `0x01` | `WDA_MONITOR` | Windows 7 | The window is only shown on a physical monitor; in captures its area is painted black. |
| `0x11` | `WDA_EXCLUDEFROMCAPTURE` | Windows 10 version 2004 (build 19041) | The window is **removed** from captures. The audience sees whatever is behind it, as if the window did not exist. |

`WDA_MONITOR` was designed for DRM-style content protection; its black rectangle is a giveaway that something is there. `WDA_EXCLUDEFROMCAPTURE` is what makes a private overlay practical.

Invisipal tries `WDA_EXCLUDEFROMCAPTURE` first. If the call fails (older Windows 10), it falls back to `WDA_MONITOR` and the header badge turns amber: `● blacked out`. If both fail the badge is red `● VISIBLE`. The same states are re-read from the window with `GetWindowDisplayAffinity`, which is how the watchdog verifies that the protection is really in place rather than assuming it.

### Which capture paths honor it

The exclusion is enforced where the screen is composed, by the Desktop Window Manager (DWM), not by each application. Capture methods that read the composed desktop therefore never see the window:

- **Windows.Graphics.Capture** (the modern API behind many recorders and, depending on the version, meeting apps)
- **DXGI Desktop Duplication** (used by OBS "Display Capture", remote-control tools and many recorders)
- **GDI `BitBlt` of the desktop** (classic screenshot code, Python `PIL.ImageGrab`)

In testing on Windows 11 25H2, a GDI/PIL grab of the window's rectangle returned the desktop behind it. The other two paths are documented to behave the same way, but the supported guarantee is Microsoft's; verify your own meeting app with the test in the README.

What it cannot affect: anything outside the PC's compositor. A phone camera, an HDMI/DisplayPort capture card or splitter, or a person looking at your monitor all see the real pixels sent to the display.

If you share a single window, only that window's content is captured, so there is nothing to exclude.

## Why the window starts at alpha 0

The affinity can only be set on an existing window handle, and Tk creates and maps the window before Python gets a chance to call anything. If the window were visible during that interval, a screen share that is already running could capture a few frames of it.

So `InvisipalApp.run()`:

1. Makes the root window borderless (`overrideredirect`) and sets `-alpha 0.0` (fully transparent) **before** it is first drawn.
2. Calls `update()` so the native window exists, and finds its handle.
3. Applies the taskbar/Alt+Tab style and then `SetWindowDisplayAffinity`.
4. Only then sets `-alpha` to the configured opacity.

A fully transparent window shows nothing even without protection, so there is no moment in which content is visible and unprotected.

## Two layers: background and text opacity

A layered window has a single alpha value, so with one window the text always fades together with the background. To control them separately Invisipal uses two top-level windows, both capture-excluded:

- **Backdrop** (a `Toplevel`): just the background color and border. Its window alpha is `background_opacity`. At `0` it is withdrawn instead, so it doesn't catch clicks.
- **Text layer** (the root window): the reader, header, footer and card index. Its background is painted in a *key color* one step away from the theme background, and `-transparentcolor` makes every pixel of exactly that color fully transparent (`LWA_COLORKEY`). Its window alpha is `text_opacity`.

The text layer is made an **owned window** of the backdrop (`GWLP_HWNDPARENT`), which makes Windows keep it directly above the backdrop in the z-order. A `<Configure>` handler and the watchdog keep the backdrop at exactly the same rectangle. Clicks on the see-through parts land on the backdrop, which forwards them (focus, scrolling, dragging to move).

Color keying is binary, so anti-aliased text edges, which blend toward the key color, stay opaque. Because the key is the background color, that edge is a thin dark outline: invisible at normal background opacity, and a subtitle-like outline when the background is very transparent.

## Finding the right window handle

Tk's `root.winfo_id()` returns the handle of an **inner child window**, not of the top-level window that Windows shows on screen. `SetWindowDisplayAffinity` and extended-style changes only work on the top-level window, so Invisipal climbs to it with `GetAncestor(hwnd, GA_ROOT)` (`win32.toplevel_hwnd`).

Tk can also recreate that wrapper window (for example around style changes or when a window is withdrawn and shown again). Because affinity is a property of the native window, a replacement window would start unprotected. The **watchdog** (`InvisipalApp._watchdog`, once per second) therefore re-resolves the handle, re-checks the affinity and re-applies it if it is missing, and re-applies click-through. `show()` does the same immediately after bringing the window back.

## Layered window and click-through

Translucency uses Tk's `-alpha`, which sets `WS_EX_LAYERED` with a constant alpha. Click-through adds `WS_EX_TRANSPARENT` so that mouse events fall through to the window below; turning it off removes only that flag, keeping the layered style that alpha needs.

The taskbar button and the Alt+Tab entry are removed by giving the window `WS_EX_TOOLWINDOW` (and clearing `WS_EX_APPWINDOW`). This matters because the taskbar is part of the screen you share: a visible "Invisipal" button would reveal that it is running. Extended style changes are followed by `SetWindowPos(... SWP_FRAMECHANGED ...)` so Windows applies them.

## Global hotkeys

`hotkeys.HotkeyThread` is a daemon thread that:

1. Forces creation of its message queue (`PeekMessageW` with `PM_NOREMOVE`).
2. Calls `RegisterHotKey(NULL, id, modifiers, vk)` for every configured binding. Registering with a NULL window handle posts `WM_HOTKEY` to the registering thread's queue. Failures (the combination is owned by another application) are collected and shown in the help view.
3. Loops on `MsgWaitForMultipleObjects`, waiting for either a message or the single-instance event, and drains the queue with `PeekMessageW`.
4. Hands each action to the UI thread through a `queue.Queue`; Tk is only ever touched from the main thread, which polls the queue every 40 ms.

A dedicated thread is used so the hotkeys do not depend on Tk's event loop or on the window being visible or focused. All bindings except the size and opacity ones use `MOD_NOREPEAT`, so holding `Ctrl+Alt+Right` does not skip through the whole guide while the size and opacity hotkeys keep repeating while held. On exit the thread is woken with `WM_QUIT` and unregisters its hotkeys.

### AltGr detection

On keyboard layouts that have an AltGr key, Windows represents AltGr internally as Left Ctrl + Right Alt. A registered `Ctrl+Alt+Q` hotkey therefore also matches `AltGr+Q`, which on Spanish, Latin American and German layouts types `@`. The hotkey would swallow the keystroke system-wide.

`win32.ctrl_alt_produces_char(vk)` asks the active layout what that combination would type: it builds a 256-byte key-state array with Ctrl and Alt pressed, maps the virtual key to a scan code with `MapVirtualKeyExW`, and calls `ToUnicodeEx` with flag `0x4` (do not modify the keyboard state, which avoids dead-key side effects). If it returns a printable character, the combination is in conflict. `hotkeys.resolve_altgr_conflicts` then moves exactly the affected `Ctrl+Alt+<key>` hotkeys to `Ctrl+Alt+Shift+<key>` and records a note for the UI. The check runs once at startup using the layout of the main thread, so switching layouts afterwards is not re-evaluated; restart Invisipal after changing layouts. It can be turned off with `avoid_altgr_conflicts`.

## Single instance

At startup `claim_single_instance` creates a named event, `Local\Invisipal.SingleInstance.v1` (per user session). If it already existed (`ERROR_ALREADY_EXISTS`), this process is the second one: it signals the event and exits. In the running process the hotkey thread is also waiting on that event handle, and when it fires it posts a `show` action to the UI, which brings the window back without stealing focus. This is why launching Invisipal again is a safe way to recover a hidden window.

## Not stealing focus

`show()` remembers the current foreground window, shows and lifts Invisipal, re-checks protection, and then restores the previous foreground window. Combined with the hotkeys never requiring focus, the meeting application keeps keyboard focus (and, for example, its mute/unmute shortcuts) while you flip through cards.

## Persistence

`config.json` and each guide are written to a temporary file and moved into place with `os.replace`, so an interruption never leaves a half-written file. Window geometry is read from the real window rectangle (`GetWindowRect`) because Tk's coordinates are off for borderless windows, and a saved position that does not land on any monitor (for example after disconnecting a display) is discarded in favor of the default top-right placement. The process opts into system DPI awareness before Tk starts so text is sharp on high-DPI displays and the pixel sizes in `config.json` are physical pixels.
