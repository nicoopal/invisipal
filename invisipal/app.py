"""The Invisipal window: a borderless, translucent, capture-excluded card reader."""

from __future__ import annotations

import os
import queue
import time
import tkinter as tk
import tkinter.font as tkfont
from datetime import datetime
from pathlib import Path

from . import __version__, hotkeys, layout, markdown, win32
from . import cards as cardlib
from .config import (
    BACKGROUND_MIN,
    FONT_MAX,
    FONT_MIN,
    INDEX_FONT_MAX,
    INDEX_FONT_MIN,
    OPACITY_MAX,
    SPLIT_MODES,
    TEXT_MIN,
    Config,
)
from .guides import GuideLibrary

FALLBACK_GUIDE = """# Welcome to Invisipal

This window is **hidden from screen sharing**.

Press `Ctrl+Alt+→` for the next card.

---

## Next steps

- Press **E** to edit this guide
- Press **L** to open the guide library
- Press **?** for every shortcut
"""

ASSETS = Path(__file__).resolve().parent / "assets"
FONT_STEP = 2
OPACITY_STEP = 0.05
MIN_W, MIN_H = 280, 160

LOCAL_KEYS = [
    ("→  ↓  Space  PgDn", "next card"),
    ("←  ↑  Backspace  PgUp", "previous card"),
    ("Home / End", "first / last card"),
    ("+ / −   Ctrl+Wheel", "bigger / smaller text"),
    ("Alt+Wheel", "background opacity"),
    ("Alt+Shift+Wheel", "text opacity"),
    ("A", "appearance sliders (background, text, size)"),
    ("I", "show / hide the card index"),
    ("E", "edit this guide (Ctrl+S saves, Ctrl+Enter card break, Esc cancels)"),
    ("L", "guide library"),
    ("Ctrl+V", "paste clipboard as a new guide"),
    ("F5", "reload from disk"),
    ("?", "this help"),
]

ACTION_LABELS = {
    "next": "next card (scrolls long cards first)",
    "prev": "previous card",
    "font_up": "bigger text",
    "font_down": "smaller text",
    "toggle": "show / hide window",
    "reload": "reload guide from disk",
    "quit": "quit",
    "first": "first card",
    "last": "last card",
    "background_more": "background more opaque",
    "background_less": "background more transparent",
    "text_more": "text more opaque",
    "text_less": "text more transparent",
    "snap_top_left": "move to top left",
    "snap_top_right": "move to top right",
    "snap_bottom_right": "move to bottom right",
    "snap_bottom_left": "move to bottom left",
    "snap_top_center": "move to top center (near the webcam)",
    "snap_bottom_center": "move to bottom center",
    "toggle_index": "show / hide card index",
    "click_through": "click-through on / off",
    "next_guide": "switch to next guide",
    "timer": "start / pause timer",
}

PROTECTION_BADGES = {
    "excluded": ("● private", "ok"),
    "blackout": ("● blacked out", "warn"),
    "off": ("● VISIBLE", "warn"),
    "failed": ("● VISIBLE", "danger"),
    "pending": ("● …", "muted"),
}


class InvisipalApp:
    def __init__(self, base_dir: Path, cfg: Config, wake_event=None, protect: bool | None = None):
        self.base_dir = base_dir
        self.cfg = cfg
        self.theme = cfg["theme"]
        self.wake_event = wake_event
        self.protect = cfg["capture_protection"] if protect is None else protect
        self.library = GuideLibrary(base_dir / cfg["guides_dir"])

        self.actions: queue.Queue[str] = queue.Queue()
        self.hotkey_thread: hotkeys.HotkeyThread | None = None
        self.hotkey_errors: list[str] = []
        self.hotkey_warnings: list[str] = []
        self.hotkey_list: list[hotkeys.Hotkey] = []

        self.hwnd = 0
        self.key = layout.key_color(self.theme["background"])  # fully transparent color
        self.backdrop: tk.Toplevel | None = None  # translucent background layer
        self.backdrop_hwnd = 0
        self.appearance_open = False
        self._index_hover = None
        self.visible = True
        self.click_through = False
        self.protection = "pending"
        self.view = "reader"
        self.guide_name: str | None = None
        self.guide_text = ""
        self.guide_mtime = 0.0
        self.cards: list[cardlib.Card] = []
        self.index = 0
        self.timer_started: float | None = None
        self.timer_elapsed = 0.0
        self._toast_job = None
        self._save_job = None
        self._drag = (0, 0)
        self._resize = (0, 0, 0, 0)

        self.root = tk.Tk()
        self.root.title("Invisipal")
        try:
            self.root.iconbitmap(default=str(ASSETS / "invisipal.ico"))
        except tk.TclError:
            pass
        self._init_fonts()
        self._build_ui()

    # ------------------------------------------------------------------ setup
    def _init_fonts(self) -> None:
        families = set(tkfont.families(self.root))
        body = self.cfg["font_family"] if self.cfg["font_family"] in families else "Segoe UI"
        mono = next((f for f in (self.cfg["mono_family"], "Cascadia Mono", "Consolas") if f in families), "Courier New")
        self.fonts = {
            "body": tkfont.Font(self.root, family=body),
            "body_b": tkfont.Font(self.root, family=body, weight="bold"),
            "body_i": tkfont.Font(self.root, family=body, slant="italic"),
            "body_b_i": tkfont.Font(self.root, family=body, weight="bold", slant="italic"),
            "h1": tkfont.Font(self.root, family=body, weight="bold"),
            "h2": tkfont.Font(self.root, family=body, weight="bold"),
            "h3": tkfont.Font(self.root, family=body, weight="bold"),
            "mono": tkfont.Font(self.root, family=mono),
            "gap": tkfont.Font(self.root, family=body),
        }
        self.ui_font = tkfont.Font(self.root, family="Segoe UI", size=10)
        self.ui_bold = tkfont.Font(self.root, family="Segoe UI Semibold", size=10)
        self.icon_font = tkfont.Font(self.root, family="Segoe UI Symbol", size=11)
        self.editor_font = tkfont.Font(self.root, family=mono, size=11)
        self.index_font = tkfont.Font(self.root, family=body, size=self.cfg["index_font_size"])
        self.index_bold = tkfont.Font(self.root, family=body, size=self.cfg["index_font_size"], weight="bold")
        self._apply_font_size()

    def _apply_font_size(self) -> None:
        size = self.cfg["font_size"]
        scale = {"body": 1, "body_b": 1, "body_i": 1, "body_b_i": 1,
                 "h1": 1.55, "h2": 1.3, "h3": 1.12, "mono": 0.9, "gap": 0.45}
        for name, factor in scale.items():
            self.fonts[name].configure(size=max(6, round(size * factor)))

    def _build_ui(self) -> None:
        t = self.theme
        root = self.root
        # Everything painted in the key color is fully transparent; the separate
        # backdrop window underneath provides the (translucent) background.
        root.configure(bg=self.key)
        self.frame = tk.Frame(root, bg=self.key)
        self.frame.pack(fill="both", expand=True, padx=1, pady=1)

        # Header: drag handle + status + buttons
        self.header = tk.Frame(self.frame, bg=t["surface"])
        self.header.pack(fill="x", side="top")
        try:
            self.logo = tk.PhotoImage(file=str(ASSETS / "header.png"))
        except tk.TclError:
            self.logo = None
        self.index_btn = self._button(self.header, "◧", self.toggle_index, font=self.icon_font, padx=6)
        self.index_btn.pack(side="left", padx=(2, 0))
        self.logo_label = tk.Label(self.header, image=self.logo, bg=t["surface"], padx=0)
        if self.logo:
            self.logo_label.pack(side="left", padx=(2, 0))
        self.title_label = tk.Label(self.header, text="Invisipal", bg=t["surface"], fg=t["accent"],
                                    font=self.ui_bold, padx=6 if self.logo else 10, pady=5)
        self.title_label.pack(side="left")
        self.guide_label = tk.Label(self.header, text="", bg=t["surface"], fg=t["muted"],
                                    font=self.ui_font, pady=5, cursor="hand2")
        self.guide_label.pack(side="left")
        self.guide_label.bind("<Button-1>", lambda e: self.show_view("library"))

        self.quit_btn = self._button(self.header, "✕", self.quit, font=self.icon_font, hover_fg=t["danger"])
        self.hide_btn = self._button(self.header, "—", self.hide, font=self.icon_font)
        self.help_btn = self._button(self.header, "?", lambda: self.show_view("help"), font=self.ui_bold)
        self.edit_btn = self._button(self.header, "✎", lambda: self.show_view("editor"), font=self.icon_font)
        self.lib_btn = self._button(self.header, "☰", lambda: self.show_view("library"), font=self.icon_font)
        self.look_btn = self._button(self.header, "◐", self.toggle_appearance, font=self.icon_font)
        self.counter = tk.Label(self.header, text="0 / 0", bg=t["surface"], fg=t["text"],
                                font=self.ui_bold, padx=8)
        self.timer_label = self._button(self.header, "00:00", self.toggle_timer, font=self.ui_font)
        self.timer_label.bind("<Double-Button-1>", lambda e: self.reset_timer())
        self.badge = self._button(self.header, "● …", lambda: self.show_view("help"), font=self.ui_font)
        for widget in (self.quit_btn, self.hide_btn, self.help_btn, self.edit_btn, self.lib_btn,
                       self.look_btn, self.counter, self.timer_label, self.badge):
            widget.pack(side="right")
        for widget in (self.header, self.logo_label, self.title_label):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_move)
            widget.bind("<ButtonRelease-1>", lambda e: self._schedule_save())

        self.progress = tk.Canvas(self.frame, height=3, bg=t["surface"], highlightthickness=0, bd=0)
        self.progress.pack(fill="x", side="top")
        self.progress.bind("<Configure>", lambda e: self._draw_progress())
        self._build_appearance()

        # Footer: prev / status / next / resize grip
        self.footer = tk.Frame(self.frame, bg=t["surface"])
        self.footer.pack(fill="x", side="bottom")
        self.prev_btn = self._button(self.footer, "‹", self.prev_card, font=self.icon_font, padx=12)
        self.prev_btn.pack(side="left")
        self.grip = tk.Label(self.footer, text="◢", bg=t["surface"], fg=t["border"],
                             font=self.ui_font, cursor="size_nw_se", padx=3)
        self.grip.pack(side="right", anchor="se")
        self.grip.bind("<ButtonPress-1>", self._resize_start)
        self.grip.bind("<B1-Motion>", self._resize_move)
        self.grip.bind("<ButtonRelease-1>", lambda e: self._schedule_save())
        self.next_btn = self._button(self.footer, "›", self.next_card, font=self.icon_font, padx=12)
        self.next_btn.pack(side="right")
        self.status = tk.Label(self.footer, text="", bg=t["surface"], fg=t["muted"],
                               font=self.ui_font, anchor="center")
        self.status.pack(side="left", fill="x", expand=True)

        self.body = tk.Frame(self.frame, bg=self.key)
        self.body.pack(fill="both", expand=True)
        self._build_reader()
        self._build_editor()
        self._build_library()
        self._build_help()
        self.views = {"reader": self.reader_pane, "editor": self.editor_frame,
                      "library": self.library_frame, "help": self.help_frame}
        self.reader_pane.pack(fill="both", expand=True)

        root.bind("<Configure>", self._on_root_configure, add="+")
        root.bind("<Key>", self._on_key)
        root.bind("<Escape>", lambda e: self.leave_view())

    def _button(self, parent, text, command, font=None, padx=7, hover_fg=None):
        t = self.theme
        lbl = tk.Label(parent, text=text, bg=parent["bg"], fg=t["muted"], font=font or self.ui_font,
                       padx=padx, pady=4, cursor="hand2")
        lbl.normal_fg = t["muted"]
        lbl.bind("<Button-1>", lambda e: command())
        lbl.bind("<Enter>", lambda e: lbl.config(fg=hover_fg or t["text"], bg=t["border"]))
        lbl.bind("<Leave>", lambda e: lbl.config(fg=lbl.normal_fg, bg=parent["bg"]))
        return lbl

    @staticmethod
    def _set_fg(label, color) -> None:
        label.normal_fg = color
        label.config(fg=color)

    def _text_widget(self, parent, **kw) -> tk.Text:
        t = self.theme
        options = dict(bg=t["background"], fg=t["text"], bd=0, highlightthickness=0, wrap="word",
                       padx=26, pady=18, cursor="arrow", insertwidth=0, takefocus=True,
                       selectbackground=t["border"], selectforeground=t["text"], inactiveselectbackground=t["border"])
        options.update(kw)
        return tk.Text(parent, **options)

    def _build_reader(self) -> None:
        t = self.theme
        # Card index on the left, the card itself on the right; the sash resizes the index.
        self.reader_pane = tk.PanedWindow(self.body, orient="horizontal", bg=t["border"], bd=0,
                                          sashwidth=3, sashrelief="flat", showhandle=False, opaqueresize=True)
        # A real (non-key) background: color-keyed pixels let clicks and the wheel fall
        # through to the window behind, which made the titles hard to click and scroll.
        self.index_list = self._text_widget(self.reader_pane, bg=t["surface"], fg=t["muted"], font=self.index_font,
                                            wrap="none", padx=6, pady=10, spacing1=5, spacing3=5, cursor="hand2")
        ix = self.index_list
        ix.tag_configure("num", foreground=t["muted"])
        ix.tag_configure("row_current", background=t["code_bg"])
        ix.tag_configure("current", foreground=t["accent"], font=self.index_bold)
        ix.tag_configure("hover", background=t["border"], foreground=t["text"])
        ix.bind("<Button-1>", self._on_index_click)
        ix.bind("<Motion>", self._on_index_motion)
        ix.bind("<Leave>", lambda e: self._set_index_hover(None))
        ix.bind("<MouseWheel>", self._on_wheel)
        ix.bind("<Control-MouseWheel>", self._on_index_ctrl_wheel)
        self.reader = self._text_widget(self.reader_pane, bg=self.key)
        self.reader_pane.add(self.index_list, width=self.cfg["index_width"], minsize=60, stretch="never")
        self.reader_pane.add(self.reader, minsize=140, stretch="always")
        if not self.cfg["index_visible"]:
            self.reader_pane.forget(self.index_list)
        self.reader_pane.bind("<ButtonRelease-1>", self._on_sash_release)
        r = self.reader
        r.tag_configure("body", font=self.fonts["body"])
        r.tag_configure("body_b", font=self.fonts["body_b"])
        r.tag_configure("body_i", font=self.fonts["body_i"])
        r.tag_configure("body_b_i", font=self.fonts["body_b_i"])
        r.tag_configure("mono", font=self.fonts["mono"])
        r.tag_configure("gap", font=self.fonts["gap"])
        for level in ("h1", "h2", "h3"):
            r.tag_configure(level, font=self.fonts[level], foreground=t["heading"])
        r.tag_configure("marker", foreground=t["accent"])
        r.tag_configure("code", background=t["code_bg"], foreground=t["code_fg"])
        r.tag_configure("codeblock", background=t["code_bg"], foreground=t["code_fg"], lmargin1=12, lmargin2=12)
        r.tag_configure("quote", foreground=t["quote"])
        r.tag_configure("quote_bar", foreground=t["accent"])
        r.tag_configure("mark", background=t["highlight_bg"], foreground=t["highlight_fg"])
        r.tag_configure("strike", overstrike=True)
        r.tag_configure("done", foreground=t["muted"], overstrike=True)
        r.tag_configure("rule", foreground=t["border"], justify="center")
        r.tag_configure("empty", foreground=t["muted"], font=self.fonts["body_i"])
        r.bind("<Configure>", lambda e: self.root.after_idle(self._update_hint))
        r.bind("<Button-1>", lambda e: (self.root.focus_force(), r.focus_set()), add="+")
        r.bind("<MouseWheel>", self._on_wheel)
        r.bind("<Control-MouseWheel>", self._on_ctrl_wheel)
        r.bind("<Alt-MouseWheel>", self._on_alt_wheel)
        r.bind("<Alt-Shift-MouseWheel>", self._on_alt_shift_wheel)

    def _build_editor(self) -> None:
        t = self.theme
        self.editor_frame = tk.Frame(self.body, bg=t["background"])
        bar = tk.Frame(self.editor_frame, bg=t["background"])
        bar.pack(fill="x", padx=10, pady=(8, 4))
        save = self._button(bar, "Save  Ctrl+S", self.save_editor, font=self.ui_bold)
        self._set_fg(save, t["accent"])
        save.pack(side="left")
        self._button(bar, "Cancel", self.leave_view).pack(side="left")
        self._button(bar, "+ Card break", self.insert_card_break).pack(side="left")
        self._button(bar, "Replace with clipboard", self.replace_with_clipboard).pack(side="left")
        self.split_btn = self._button(bar, "", self.cycle_split_mode)
        self.split_btn.pack(side="left")
        self.editor_info = tk.Label(bar, text="", bg=t["background"], fg=t["muted"], font=self.ui_font)
        self.editor_info.pack(side="right")

        self.editor = self._text_widget(self.editor_frame, bg=t["surface"], font=self.editor_font, padx=14,
                                        pady=10, cursor="xterm", insertwidth=2, insertbackground=t["text"],
                                        undo=True, autoseparators=True, maxundo=-1, spacing2=2)
        self.editor.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.editor.bind("<Control-s>", lambda e: (self.save_editor(), "break")[1])
        self.editor.bind("<Control-Return>", lambda e: (self.insert_card_break(), "break")[1])
        self.editor.bind("<<Modified>>", self._on_editor_modified)
        self.editor.bind("<Control-a>", lambda e: (self.editor.tag_add("sel", "1.0", "end-1c"), "break")[1])
        self._editor_dirty = False
        self._discard_armed = False

    def _build_library(self) -> None:
        t = self.theme
        self.library_frame = tk.Frame(self.body, bg=t["background"])
        bar = tk.Frame(self.library_frame, bg=t["background"])
        bar.pack(fill="x", padx=10, pady=(8, 4))
        tk.Label(bar, text="Guides", bg=t["background"], fg=t["text"],
                 font=self.ui_bold).pack(side="left", padx=(6, 10))
        self._button(bar, "+ New", self._show_new_entry).pack(side="left")
        self._button(bar, "Paste as new", self.paste_as_new_guide).pack(side="left")
        self._button(bar, "Open folder", self.open_guides_folder).pack(side="left")
        self._button(bar, "Back", lambda: self.show_view("reader")).pack(side="right")

        self.new_row = tk.Frame(self.library_frame, bg=t["background"])
        tk.Label(self.new_row, text="Name:", bg=t["background"], fg=t["muted"],
                 font=self.ui_font).pack(side="left", padx=(16, 6))
        self.new_entry = tk.Entry(self.new_row, bg=t["surface"], fg=t["text"], insertbackground=t["text"],
                                  relief="flat", font=self.ui_font, highlightthickness=1,
                                  highlightbackground=t["border"], highlightcolor=t["accent"])
        self.new_entry.pack(side="left", fill="x", expand=True, ipady=3)
        self.new_entry.bind("<Return>", lambda e: self._create_from_entry())
        self.new_entry.bind("<Escape>", lambda e: (self.new_row.pack_forget(), "break")[1])
        self._button(self.new_row, "Create", self._create_from_entry).pack(side="left", padx=(6, 10))

        self.library_list = self._text_widget(self.library_frame, font=self.ui_font, padx=16, pady=6,
                                              spacing1=4, spacing3=4, wrap="none")
        self.library_list.pack(fill="both", expand=True)

    def _build_help(self) -> None:
        t = self.theme
        self.help_frame = tk.Frame(self.body, bg=t["background"])
        self.help_text = self._text_widget(self.help_frame, font=self.ui_font, padx=18, pady=10, spacing1=2)
        self.help_text.pack(fill="both", expand=True)
        h = self.help_text
        h.tag_configure("title", font=self.ui_bold, foreground=t["text"], spacing1=10)
        h.tag_configure("key", foreground=t["accent"])
        h.tag_configure("muted", foreground=t["muted"])
        h.tag_configure("bad", foreground=t["danger"])
        h.tag_configure("warn", foreground=t["warn"])
        h.tag_configure("ok", foreground=t["ok"])
        h.bind("<MouseWheel>", self._on_wheel)

    # -------------------------------------------------------------- lifecycle
    def run(self) -> None:
        root = self.root
        root.overrideredirect(True)
        root.attributes("-alpha", 0.0)  # stay invisible until capture exclusion is active
        root.attributes("-transparentcolor", self.key)
        root.attributes("-topmost", bool(self.cfg["always_on_top"]))
        root.minsize(MIN_W, MIN_H)
        root.geometry(self._initial_geometry())
        self._create_backdrop()

        self.load_initial_guide()
        root.update()

        self._refresh_hwnd()
        win32.set_taskbar_visible(self.hwnd, bool(self.cfg["show_in_taskbar"]))
        if self.cfg["show_in_taskbar"]:
            root.withdraw()
            root.deiconify()
            root.update()
            self._refresh_hwnd()
        self._link_backdrop()
        self._ensure_protection(force=True)
        self._apply_opacity()

        self._start_hotkeys()
        if self.cfg.load_error:
            self.toast(self.cfg.load_error, "danger", 6000)
        elif self.hotkey_thread and self.hotkey_thread.failed:
            failed = self.hotkey_thread.failed
            what = failed[0] if len(failed) == 1 else f"{len(failed)} hotkeys"
            self.toast(f"{what} in use by another app — press ? for details", "warn", 6000)
        elif self.hotkey_warnings:
            self.toast(self.hotkey_warnings[0], "warn", 8000)

        root.after(40, self._poll_actions)
        root.after(1000, self._watchdog)
        root.after(500, self._tick_timer)
        self.reader.focus_set()
        root.mainloop()

    def _initial_geometry(self) -> str:
        w, h = self.cfg["width"], self.cfg["height"]
        x, y = self.cfg["x"], self.cfg["y"]
        if x is None or y is None or not win32.rect_is_on_screen(int(x), int(y), w, h):
            x = max(0, self.root.winfo_screenwidth() - w - 48)
            y = 72
        return f"{w}x{h}+{int(x)}+{int(y)}"

    def _start_hotkeys(self) -> None:
        if not win32.IS_WINDOWS:
            return
        keys, self.hotkey_errors = hotkeys.build_hotkeys(self.cfg["hotkeys"])
        keys, self.hotkey_warnings = hotkeys.resolve_altgr_conflicts(keys, self.cfg["avoid_altgr_conflicts"])
        self.hotkey_list = keys
        self.hotkey_thread = hotkeys.HotkeyThread(keys, self.actions.put, self.wake_event)
        self.hotkey_thread.start()
        self.hotkey_thread.ready.wait(timeout=2.0)

    def quit(self) -> None:
        self._store_geometry()
        self._save_now()
        if self.hotkey_thread:
            self.hotkey_thread.stop()
        self.root.destroy()

    # ------------------------------------------------------------ win32 glue
    def _refresh_hwnd(self) -> None:
        self.hwnd = win32.toplevel_hwnd(self.root.winfo_id())

    def _ensure_protection(self, force: bool = False) -> None:
        if not win32.IS_WINDOWS:
            return
        wanted = "excluded" if self.protect else "off"
        statuses = []
        for hwnd in (self.hwnd, self.backdrop_hwnd):
            if not hwnd:
                continue
            status = win32.affinity_status(hwnd, self.protect)
            if force or status not in (wanted, "blackout"):
                status = win32.set_capture_excluded(hwnd, self.protect)
            statuses.append(status)
        if not statuses:
            return
        # The badge reports the weakest of the two layers.
        status = next((s for s in ("failed", "off", "blackout") if s in statuses), statuses[0])
        if status != self.protection:
            self.protection = status
            text, color = PROTECTION_BADGES[status]
            self.badge.config(text=text)
            self._set_fg(self.badge, self.theme[color] if color in self.theme else self.theme["muted"])

    def _watchdog(self) -> None:
        """Tk can recreate its wrapper window; keep affinity + styles applied."""
        try:
            self._refresh_hwnd()
            self._link_backdrop()
            self._ensure_protection()
            if self.click_through:
                for hwnd in (self.hwnd, self.backdrop_hwnd):
                    if hwnd:
                        win32.set_click_through(hwnd, True)
            self._check_file_changed()
        finally:
            self.root.after(1000, self._watchdog)

    def _poll_actions(self) -> None:
        try:
            while True:
                self.dispatch(self.actions.get_nowait())
        except queue.Empty:
            pass
        self.root.after(40, self._poll_actions)

    def dispatch(self, action: str) -> None:
        handler = {
            "next": self.next_card, "prev": self.prev_card,
            "first": lambda: self.go_to(0), "last": lambda: self.go_to(len(self.cards) - 1),
            "font_up": lambda: self.change_font(FONT_STEP), "font_down": lambda: self.change_font(-FONT_STEP),
            "background_more": lambda: self.change_background(OPACITY_STEP),
            "background_less": lambda: self.change_background(-OPACITY_STEP),
            "text_more": lambda: self.change_text_opacity(OPACITY_STEP),
            "text_less": lambda: self.change_text_opacity(-OPACITY_STEP),
            "toggle_index": self.toggle_index,
            **{f"snap_{where}": (lambda w=where: self.snap(w)) for where in layout.SNAP_POSITIONS},
            "toggle": self.toggle_visible, "show": self.show, "reload": self.reload,
            "quit": self.quit, "click_through": self.toggle_click_through,
            "next_guide": self.next_guide, "timer": self.toggle_timer,
        }.get(action)
        if handler:
            handler()

    # ----------------------------------------------------------- visibility
    def hide(self) -> None:
        if self.visible:
            self._store_geometry()
            self.root.withdraw()
            if self.backdrop:
                self.backdrop.withdraw()
            self.visible = False

    def show(self) -> None:
        previous = win32.foreground_window() if win32.IS_WINDOWS else 0
        if not self.visible:
            # Re-appear fully transparent and only fade in once protection is confirmed.
            self.root.attributes("-alpha", 0.0)
            self.root.deiconify()
            self.visible = True
        self.root.attributes("-topmost", bool(self.cfg["always_on_top"]))
        self.root.lift()
        self.root.update_idletasks()
        self._refresh_hwnd()
        self._link_backdrop()
        self._ensure_protection()
        self._apply_opacity()
        if previous and previous != self.hwnd:
            win32.restore_foreground(previous)  # don't steal focus from the meeting app

    def toggle_visible(self) -> None:
        self.hide() if self.visible else self.show()

    def toggle_click_through(self) -> None:
        self.click_through = not self.click_through
        if win32.IS_WINDOWS:
            for hwnd in (self.hwnd, self.backdrop_hwnd):
                if hwnd:
                    win32.set_click_through(hwnd, self.click_through)
        self.title_label.config(text="Invisipal  ⇣ click-through" if self.click_through else "Invisipal")
        self.toast("Click-through ON — mouse passes through" if self.click_through else "Click-through OFF")

    def change_background(self, delta: float) -> None:
        self.set_background(self.cfg["background_opacity"] + delta)
        self.toast(f"Background {round(self.cfg['background_opacity'] * 100)}%")

    def change_text_opacity(self, delta: float) -> None:
        self.set_text_opacity(self.cfg["text_opacity"] + delta)
        self.toast(f"Text {round(self.cfg['text_opacity'] * 100)}%")

    def set_background(self, value: float) -> None:
        self.cfg["background_opacity"] = round(min(OPACITY_MAX, max(BACKGROUND_MIN, value)), 2)
        self._apply_opacity()
        self._schedule_save()

    def set_text_opacity(self, value: float) -> None:
        self.cfg["text_opacity"] = round(min(OPACITY_MAX, max(TEXT_MIN, value)), 2)
        self._apply_opacity()
        self._schedule_save()

    def _apply_opacity(self) -> None:
        """Text layer = root window alpha; background layer = backdrop window alpha."""
        if self.visible:
            self.root.attributes("-alpha", self.cfg["text_opacity"])
            if self.backdrop:
                background = self.cfg["background_opacity"]
                if background <= 0.0:
                    self.backdrop.withdraw()  # nothing to show, and don't catch clicks
                else:
                    if self.backdrop.state() == "withdrawn":
                        self.backdrop.attributes("-alpha", 0.0)
                        self.backdrop.deiconify()
                        self.root.update_idletasks()
                        self._link_backdrop()
                        self._ensure_protection()
                    self.backdrop.attributes("-alpha", background)
        self._update_appearance_labels()

    # -------------------------------------------------------- backdrop layer
    def _create_backdrop(self) -> None:
        t = self.theme
        b = tk.Toplevel(self.root)
        b.overrideredirect(True)
        b.attributes("-alpha", 0.0)
        b.attributes("-topmost", bool(self.cfg["always_on_top"]))
        b.configure(bg=t["background"])
        self.backdrop_canvas = tk.Canvas(b, bg=t["background"], highlightthickness=0, bd=0, cursor="fleur")
        self.backdrop_canvas.pack(fill="both", expand=True)
        c = self.backdrop_canvas
        c.bind("<Configure>", lambda e: self._draw_backdrop())
        # Clicks on the see-through parts of the text layer land here: drag to move.
        c.bind("<ButtonPress-1>", self._on_backdrop_press)
        c.bind("<B1-Motion>", self._drag_move)
        c.bind("<ButtonRelease-1>", lambda e: self._schedule_save())
        c.bind("<MouseWheel>", self._on_backdrop_wheel)
        b.geometry(self.root.geometry())
        self.backdrop = b

    def _on_backdrop_press(self, event) -> None:
        self._drag_start(event)
        self.root.focus_force()
        self.reader.focus_set()

    def _on_backdrop_wheel(self, event) -> None:
        self.reader.yview_scroll(-1 if event.delta > 0 else 1, "units")
        self._update_hint()

    def _draw_backdrop(self) -> None:
        c = self.backdrop_canvas
        c.delete("all")
        c.create_rectangle(0, 0, c.winfo_width() - 1, c.winfo_height() - 1, outline=self.theme["border"])

    def _link_backdrop(self) -> None:
        """Keep the backdrop exactly under the text window (same rect, owned below it)."""
        if not (self.backdrop and win32.IS_WINDOWS and self.hwnd):
            return
        if self.backdrop.state() == "withdrawn":
            return
        self.backdrop_hwnd = win32.toplevel_hwnd(self.backdrop.winfo_id())
        if not self.backdrop_hwnd or self.backdrop_hwnd == self.hwnd:
            self.backdrop_hwnd = 0
            return
        win32.set_taskbar_visible(self.backdrop_hwnd, False)
        if win32.get_owner(self.hwnd) != self.backdrop_hwnd:
            if win32.get_owner(self.backdrop_hwnd) == self.hwnd:
                win32.set_owner(self.backdrop_hwnd, 0)
            win32.set_owner(self.hwnd, self.backdrop_hwnd)  # owned windows stay above their owner
            self.root.lift()
        self._sync_backdrop()

    def _sync_backdrop(self) -> None:
        if not (self.backdrop and self.hwnd):
            return
        x, y, w, h = win32.window_rect(self.hwnd)
        if w > 1 and h > 1 and self.backdrop.geometry() != f"{w}x{h}+{x}+{y}":
            self.backdrop.geometry(f"{w}x{h}+{x}+{y}")

    def _on_root_configure(self, event) -> None:
        if event.widget is self.root:
            self._sync_backdrop()

    # ------------------------------------------------------------ positions
    def snap(self, where: str) -> None:
        if not self.hwnd:
            return
        _, _, w, h = win32.window_rect(self.hwnd)
        x, y = layout.snap_position(win32.work_area(self.hwnd), (w, h), where, self.cfg["snap_margin"])
        self.root.geometry(f"+{x}+{y}")
        self.root.update_idletasks()
        self._sync_backdrop()
        self.toast(where.replace("_", " ").capitalize())
        self._schedule_save()

    # ----------------------------------------------------------- appearance
    def _build_appearance(self) -> None:
        """Inline sliders (no popups: a separate window would be capturable)."""
        t = self.theme
        bar = tk.Frame(self.frame, bg=t["surface"])
        self.appearance_bar = bar
        self.appearance_labels = {}
        self.appearance_sliders = []
        specs = [
            ("background", BACKGROUND_MIN, OPACITY_MAX, lambda: self.cfg["background_opacity"], self.set_background),
            ("text", TEXT_MIN, OPACITY_MAX, lambda: self.cfg["text_opacity"], self.set_text_opacity),
            ("size", FONT_MIN, 48, lambda: self.cfg["font_size"], self._set_font_size),
        ]
        for key, lo, hi, getter, setter in specs:
            cell = tk.Frame(bar, bg=t["surface"])
            cell.pack(side="left", padx=(12, 4), pady=(2, 6))
            label = tk.Label(cell, bg=t["surface"], fg=t["muted"], font=self.ui_font, anchor="w", width=14)
            label.pack(anchor="w")
            self.appearance_labels[key] = label
            slider = self._slider(cell, lo, hi, getter, setter)
            slider.pack(anchor="w")
            self.appearance_sliders.append(slider)
        self._update_appearance_labels()

    def _slider(self, parent, lo, hi, getter, setter, width=120) -> tk.Canvas:
        t = self.theme
        c = tk.Canvas(parent, width=width, height=14, bg=t["surface"], highlightthickness=0, bd=0, cursor="hand2")

        def draw() -> None:
            c.delete("all")
            x = 6 + (getter() - lo) / (hi - lo) * (width - 12)
            c.create_line(6, 7, width - 6, 7, fill=t["border"], width=3, capstyle="round")
            c.create_line(6, 7, x, 7, fill=t["accent"], width=3, capstyle="round")
            c.create_oval(x - 6, 1, x + 6, 13, fill=t["text"], outline="")

        def pick(event) -> None:
            setter(lo + min(1.0, max(0.0, (event.x - 6) / (width - 12))) * (hi - lo))
            draw()

        c.bind("<Button-1>", pick)
        c.bind("<B1-Motion>", pick)
        c.redraw = draw
        draw()
        return c

    def _update_appearance_labels(self) -> None:
        if not getattr(self, "appearance_labels", None):
            return
        self.appearance_labels["background"].config(text=f"Background {round(self.cfg['background_opacity'] * 100)}%")
        self.appearance_labels["text"].config(text=f"Text {round(self.cfg['text_opacity'] * 100)}%")
        self.appearance_labels["size"].config(text=f"Size {self.cfg['font_size']}")
        for slider in self.appearance_sliders:
            slider.redraw()

    def toggle_appearance(self) -> None:
        self.appearance_open = not self.appearance_open
        if self.appearance_open:
            self.appearance_bar.pack(fill="x", side="top", after=self.progress)
            self._update_appearance_labels()
        else:
            self.appearance_bar.pack_forget()

    def _set_font_size(self, value: float) -> None:
        size = int(round(value))
        if size != self.cfg["font_size"]:
            self.change_font(size - self.cfg["font_size"])

    # ----------------------------------------------------------- card index
    def toggle_index(self) -> None:
        visible = not self.cfg["index_visible"]
        if visible:
            self.cfg["index_visible"] = True
            self.reader_pane.add(self.index_list, before=self.reader, width=self.cfg["index_width"],
                                 minsize=60, stretch="never")
            self._render_index()
        else:
            self._store_index_width()
            self.cfg["index_visible"] = False
            self.reader_pane.forget(self.index_list)
        self.toast("Card index shown" if visible else "Card index hidden")
        self._schedule_save()

    def _render_index(self) -> None:
        if not self.cfg["index_visible"]:
            return
        ix = self.index_list
        ix.configure(state="normal")
        ix.delete("1.0", "end")
        digits = len(str(len(self.cards)))
        for i, card in enumerate(self.cards):
            current = ("current",) if i == self.index else ()
            ix.insert("end", f" {i + 1:>{digits}}  ", ("num",) + current)
            ix.insert("end", (card.title or "…") + "\n", current)
            if current:  # highlight the whole row, newline included, so it spans the width
                ix.tag_add("row_current", f"{i + 1}.0", f"{i + 2}.0")
        ix.configure(state="disabled")
        if self.cards:
            ix.see(f"{self.index + 1}.0")
        self._index_hover = None

    def _index_line(self, event) -> int:
        return int(self.index_list.index(f"@{event.x},{event.y}").split(".")[0]) - 1

    def _on_index_click(self, event) -> str:
        line = self._index_line(event)
        if 0 <= line < len(self.cards):
            self.go_to(line)
        return "break"

    def _on_index_motion(self, event) -> None:
        line = self._index_line(event)
        self._set_index_hover(line if 0 <= line < len(self.cards) else None)

    def _set_index_hover(self, line) -> None:
        if line == self._index_hover:
            return
        self.index_list.tag_remove("hover", "1.0", "end")
        if line is not None:
            self.index_list.tag_add("hover", f"{line + 1}.0", f"{line + 2}.0")
        self._index_hover = line

    def _on_index_ctrl_wheel(self, event) -> str:
        size = self.cfg["index_font_size"] + (1 if event.delta > 0 else -1)
        size = min(INDEX_FONT_MAX, max(INDEX_FONT_MIN, size))
        self.cfg["index_font_size"] = size
        self.index_font.configure(size=size)
        self.index_bold.configure(size=size)
        self._schedule_save()
        return "break"

    def _store_index_width(self) -> None:
        if self.cfg["index_visible"] and self.index_list.winfo_ismapped():
            self.cfg["index_width"] = max(60, self.index_list.winfo_width())

    def _on_sash_release(self, _event=None) -> None:
        self._store_index_width()
        self._schedule_save()

    def change_font(self, delta: int) -> None:
        self.cfg["font_size"] = min(FONT_MAX, max(FONT_MIN, self.cfg["font_size"] + delta))
        self._apply_font_size()
        self.render_card(keep_scroll=True)
        self.toast(f"Text size {self.cfg['font_size']}")
        self._schedule_save()

    # --------------------------------------------------------------- guides
    def load_initial_guide(self) -> None:
        self.library.ensure()
        name = self.cfg["current_guide"]
        if not self.library.exists(name):
            names = self.library.names()
            name = names[0] if names else self.library.create("guia.txt", FALLBACK_GUIDE)
        self.open_guide(name)

    def open_guide(self, name: str) -> None:
        self._remember_position()
        self.guide_name = name
        self.cfg["current_guide"] = name
        try:
            self.guide_text = self.library.read(name)
        except OSError as exc:
            self.guide_text = ""
            self.toast(f"Cannot read {name}: {exc}", "danger", 5000)
        self.guide_mtime = self.library.mtime(name)
        self.cards = cardlib.split_cards(self.guide_text, self.cfg["split_mode"])
        saved = self.cfg["positions"].get(name, 0)
        self.index = min(max(0, int(saved)), max(0, len(self.cards) - 1))
        self.guide_label.config(text=f"·  {os.path.splitext(name)[0]}")
        self.render_card()
        self._schedule_save()

    def reload(self, quiet: bool = False) -> None:
        if self.guide_name:
            keep = self.index
            self.open_guide(self.guide_name)
            self.go_to(min(keep, len(self.cards) - 1))
            if not quiet:
                self.toast(f"Reloaded {self.guide_name}  ({len(self.cards)} cards)")

    def _check_file_changed(self) -> None:
        if not (self.cfg["auto_reload"] and self.guide_name) or self.view == "editor":
            return
        mtime = self.library.mtime(self.guide_name)
        if mtime and mtime != self.guide_mtime:
            self.reload(quiet=True)
            self.toast("Guide changed on disk — reloaded")

    def next_guide(self) -> None:
        names = self.library.names()
        if not names:
            return
        current = names.index(self.guide_name) if self.guide_name in names else -1
        self.open_guide(names[(current + 1) % len(names)])
        self.toast(f"Guide: {self.guide_name}")

    def _remember_position(self) -> None:
        if self.guide_name:
            self.cfg["positions"][self.guide_name] = self.index

    # ------------------------------------------------------------ navigation
    def go_to(self, index: int) -> None:
        if not self.cards:
            return
        index = min(max(0, index), len(self.cards) - 1)
        if index != self.index:
            self.index = index
            self._remember_position()
            self._schedule_save()
        if self.view != "reader":
            self.show_view("reader")
        self.render_card()

    def next_card(self) -> None:
        # Long card? Page through it before moving on (teleprompter style).
        if self.view == "reader" and self.reader.yview()[1] < 0.999:
            self.reader.yview_scroll(1, "pages")
            self._update_hint()
            return
        if self.index >= len(self.cards) - 1:
            self.toast("Last card")
            return
        self.go_to(self.index + 1)

    def prev_card(self) -> None:
        if self.view == "reader" and self.reader.yview()[0] > 0.001:
            self.reader.yview_scroll(-1, "pages")
            self._update_hint()
            return
        if self.index <= 0:
            self.toast("First card")
            return
        self.go_to(self.index - 1)

    # --------------------------------------------------------------- render
    def render_card(self, keep_scroll: bool = False) -> None:
        r = self.reader
        top = r.yview()[0]
        px = self.root.winfo_fpixels("1p") * self.cfg["font_size"]
        # line_spacing is the total line height in ems; Segoe UI is ~1.33em on its own.
        gap = max(0, round(px * (self.cfg["line_spacing"] - 1.33)))
        r.configure(state="normal", spacing1=gap // 2, spacing2=gap, spacing3=gap - gap // 2)
        r.delete("1.0", "end")
        for level, factor in (("h1", 0.9), ("h2", 0.7), ("h3", 0.5)):
            r.tag_configure(level, spacing1=round(px * factor), spacing3=round(px * 0.3))
        if not self.cards:
            r.insert("end", "No cards yet.\n\nPress E to write or paste a guide,\nor L to pick another one.", "empty")
        else:
            for line in markdown.parse(self.cards[self.index].text):
                self._insert_line(line)
        r.configure(state="disabled")
        r.yview_moveto(top if keep_scroll else 0)
        total = len(self.cards)
        self.counter.config(text=f"{self.index + 1 if total else 0} / {total}")
        self._draw_progress()
        self._render_index()
        self.root.after_idle(self._update_hint)

    def _insert_line(self, line: markdown.Line) -> None:
        r = self.reader
        if line.kind == "blank":
            r.insert("end", "\n", "gap")
            return
        if line.kind == "rule":
            r.insert("end", "— — —\n", ("rule", "body"))
            return
        block: list[str] = []
        if line.kind in ("h1", "h2", "h3"):
            block.append(line.kind)
        elif line.kind == "code":
            block.append("codeblock")
        if line.marker:
            base = line.indent * self.fonts["body"].measure("    ")
            hang = base + self.fonts["body"].measure(line.marker + " ")
            tag = f"indent_{base}_{hang}"
            r.tag_configure(tag, lmargin1=base, lmargin2=hang)
            block.append(tag)
            r.insert("end", line.marker + " ", tuple(block) + ("marker", "body"))
        if line.kind == "quote":
            bar_width = self.fonts["body"].measure("▎  ")
            r.tag_configure("quote_indent", lmargin2=bar_width)
            block.append("quote_indent")
            r.insert("end", "▎  ", tuple(block) + ("quote_bar", "body"))
        if line.done:
            block.append("done")
        for text, tags in line.spans:
            r.insert("end", text, tuple(block) + self._span_tags(line.kind, tags))
        r.insert("end", "\n", tuple(block) + (("mono",) if line.kind == "code" else ("body",)))

    @staticmethod
    def _span_tags(kind: str, tags: frozenset) -> tuple[str, ...]:
        out: list[str] = []
        if kind == "code":
            out.append("mono")
        elif "code" in tags:
            out += ["mono", "code"]
        elif kind in ("h1", "h2", "h3"):
            out.append(kind)
        else:
            bold = "bold" in tags
            italic = "italic" in tags or kind == "quote"
            out.append("body" + ("_b" if bold else "") + ("_i" if italic else ""))
        if kind == "quote":
            out.append("quote")
        if "mark" in tags:
            out.append("mark")
        if "strike" in tags:
            out.append("strike")
        return tuple(out)

    def _draw_progress(self) -> None:
        c = self.progress
        c.delete("all")
        total = len(self.cards)
        if total:
            width = c.winfo_width() * (self.index + 1) / total
            c.create_rectangle(0, 0, width, 3, fill=self.theme["accent"], width=0)

    def _update_hint(self) -> None:
        if self._toast_job or self.view != "reader":
            return
        top, bottom = self.reader.yview()
        if bottom < 0.999:
            text = "↓ more below"
        elif self.index < len(self.cards) - 1:
            text = f"next:  {self.cards[self.index + 1].title}"
        else:
            text = "end of guide" if self.cards else ""
        self.status.config(text=text, fg=self.theme["muted"])

    def toast(self, message: str, color: str = "text", ms: int = 1800) -> None:
        if self._toast_job:
            self.root.after_cancel(self._toast_job)
        self.status.config(text=message, fg=self.theme.get(color, self.theme["text"]))
        self._toast_job = self.root.after(ms, self._end_toast)

    def _end_toast(self) -> None:
        self._toast_job = None
        self._update_hint()
        if self.view != "reader":
            self.status.config(text="")

    # ---------------------------------------------------------------- views
    def show_view(self, name: str) -> None:
        if name == self.view and name != "reader":
            name = "reader"  # clicking the same button again toggles back
        if name == "editor":
            self._open_editor()
        elif name == "library":
            self._refresh_library()
        elif name == "help":
            self._refresh_help()
        for view_name, widget in self.views.items():
            if view_name != name:
                widget.pack_forget()
        self.views[name].pack(fill="both", expand=True)
        self.view = name
        if name == "reader":
            self.reader.focus_set()
            self.render_card(keep_scroll=True)
        elif name == "editor":
            self.root.focus_force()
            self.editor.focus_set()
        else:
            self.status.config(text="")

    def leave_view(self) -> None:
        """Esc / Cancel: back to the reader, guarding unsaved editor changes."""
        if self.view == "editor" and self._editor_dirty and not self._discard_armed:
            self._discard_armed = True
            self.toast("Unsaved changes — press Esc again to discard (Ctrl+S saves)", "warn", 4000)
            return
        self.show_view("reader")

    def _on_key(self, event) -> str | None:
        if self.view != "reader":
            return None
        key, ctrl = event.keysym, bool(event.state & 0x4)
        if ctrl and key.lower() == "v":
            self.paste_as_new_guide()
        elif ctrl:
            return None
        elif key in ("Right", "space", "Next", "Down"):
            self.next_card()
        elif key in ("Left", "BackSpace", "Prior", "Up"):
            self.prev_card()
        elif key == "Home":
            self.go_to(0)
        elif key == "End":
            self.go_to(len(self.cards) - 1)
        elif key in ("plus", "equal", "KP_Add"):
            self.change_font(FONT_STEP)
        elif key in ("minus", "KP_Subtract"):
            self.change_font(-FONT_STEP)
        elif key.lower() == "e":
            self.show_view("editor")
        elif key.lower() == "l":
            self.show_view("library")
        elif key.lower() == "i":
            self.toggle_index()
        elif key.lower() == "a":
            self.toggle_appearance()
        elif key == "question" or event.char == "?":
            self.show_view("help")
        elif key == "F5":
            self.reload()
        else:
            return None
        return "break"

    def _on_wheel(self, event) -> str:
        event.widget.yview_scroll(-1 if event.delta > 0 else 1, "units")
        self.root.after_idle(self._update_hint)
        return "break"

    def _on_ctrl_wheel(self, event) -> str:
        self.change_font(FONT_STEP if event.delta > 0 else -FONT_STEP)
        return "break"

    def _on_alt_wheel(self, event) -> str:
        self.change_background(OPACITY_STEP if event.delta > 0 else -OPACITY_STEP)
        return "break"

    def _on_alt_shift_wheel(self, event) -> str:
        self.change_text_opacity(OPACITY_STEP if event.delta > 0 else -OPACITY_STEP)
        return "break"

    # --------------------------------------------------------------- editor
    def _open_editor(self) -> None:
        e = self.editor
        e.delete("1.0", "end")
        e.insert("1.0", self.guide_text)
        e.edit_reset()
        e.edit_modified(False)
        self._editor_dirty = self._discard_armed = False
        if self.cards:
            offset = self.guide_text.find(self.cards[self.index].text)
            if offset >= 0:
                e.mark_set("insert", f"1.0 + {offset} chars")
                e.see("insert")
        self._update_split_label()
        self._update_editor_info()

    def save_editor(self) -> None:
        text = self.editor.get("1.0", "end-1c")
        cursor_text = self.editor.get("1.0", "insert")
        if not self.guide_name:
            self.guide_name = self.library.create("guia.txt", text)
        try:
            self.library.write(self.guide_name, text)
        except OSError as exc:
            self.toast(f"Save failed: {exc}", "danger", 5000)
            return
        mode = cardlib.resolve_mode(text, self.cfg["split_mode"])
        self.index = max(0, len(cardlib.split_cards(cursor_text + "x", mode)) - 1)
        self.open_guide(self.guide_name)
        self.show_view("reader")
        self.toast(f"Saved {self.guide_name}  ({len(self.cards)} cards)", "ok")

    def insert_card_break(self) -> None:
        self.editor.insert("insert", "\n\n---\n\n")
        self.editor.see("insert")
        self.editor.focus_set()

    def replace_with_clipboard(self) -> None:
        clip = self._clipboard()
        if clip is None:
            return
        self.editor.edit_separator()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", clip)
        self.editor.edit_separator()
        self.toast("Replaced with clipboard — Ctrl+Z to undo")

    def cycle_split_mode(self) -> None:
        modes = list(SPLIT_MODES)
        self.cfg["split_mode"] = modes[(modes.index(self.cfg["split_mode"]) + 1) % len(modes)]
        self._update_split_label()
        self._update_editor_info()
        self._schedule_save()

    def _update_split_label(self) -> None:
        self.split_btn.config(text=f"Split: {self.cfg['split_mode']}")

    def _on_editor_modified(self, _event=None) -> None:
        if self.editor.edit_modified():
            self.editor.edit_modified(False)
            self._editor_dirty = True
            self._discard_armed = False
            self._update_editor_info()

    def _update_editor_info(self) -> None:
        text = self.editor.get("1.0", "end-1c")
        mode = cardlib.resolve_mode(text, self.cfg["split_mode"])
        count = len(cardlib.split_cards(text, mode))
        self.editor_info.config(text=f"{count} card{'s' if count != 1 else ''} · {mode}")

    # -------------------------------------------------------------- library
    def _refresh_library(self) -> None:
        t = self.theme
        lst = self.library_list
        lst.configure(state="normal")
        lst.delete("1.0", "end")
        names = self.library.names()
        if not names:
            lst.insert("end", "No guides yet. Click “+ New” or “Paste as new”.", "muted")
        for i, name in enumerate(names):
            tag = f"row{i}"
            current = name == self.guide_name
            try:
                count = len(cardlib.split_cards(self.library.read(name), self.cfg["split_mode"]))
            except OSError:
                count = 0
            modified = datetime.fromtimestamp(self.library.mtime(name)).strftime("%d %b %H:%M")
            lst.insert("end", "●  " if current else "    ", (tag, "dot"))
            lst.insert("end", name, (tag, "name_current" if current else "name"))
            lst.insert("end", f"   {count} cards · {modified}\n", (tag, "muted"))
            lst.tag_bind(tag, "<Button-1>", lambda e, n=name: (self.open_guide(n), self.show_view("reader")))
            lst.tag_bind(tag, "<Enter>", lambda e, tg=tag: lst.tag_configure(tg, background=t["surface"]))
            lst.tag_bind(tag, "<Leave>", lambda e, tg=tag: lst.tag_configure(tg, background=""))
        lst.tag_configure("dot", foreground=t["accent"])
        lst.tag_configure("name", foreground=t["text"])
        lst.tag_configure("name_current", foreground=t["accent"], font=self.ui_bold)
        lst.tag_configure("muted", foreground=t["muted"])
        lst.configure(state="disabled", cursor="hand2")

    def _show_new_entry(self) -> None:
        self.new_row.pack(fill="x", pady=(0, 6), before=self.library_list)
        self.new_entry.delete(0, "end")
        self.root.focus_force()
        self.new_entry.focus_set()

    def _create_from_entry(self) -> None:
        wanted = self.new_entry.get().strip()
        if not wanted:
            return
        self.new_row.pack_forget()
        name = self.library.create(wanted)
        self.open_guide(name)
        self.show_view("editor")
        self.toast(f"Created {name}", "ok")

    def paste_as_new_guide(self) -> None:
        clip = self._clipboard()
        if clip is None:
            return
        name = self.library.create(f"pasted-{datetime.now():%Y-%m-%d-%H%M}.md", clip)
        self.open_guide(name)
        self.show_view("reader")
        self.toast(f"New guide {name}  ({len(self.cards)} cards)", "ok", 3000)

    def open_guides_folder(self) -> None:
        self.library.ensure()
        os.startfile(self.library.folder)  # noqa: S606 - opens Explorer

    def _clipboard(self) -> str | None:
        try:
            clip = self.root.clipboard_get()
        except tk.TclError:
            clip = ""
        if not clip.strip():
            self.toast("Clipboard is empty", "warn")
            return None
        return clip

    # ----------------------------------------------------------------- help
    def _refresh_help(self) -> None:
        h = self.help_text
        h.configure(state="normal", tabs=(self.ui_font.measure("Ctrl+Alt+Shift+PageDown") + 16,))
        h.delete("1.0", "end")
        status_text = {
            "excluded": ("Hidden from screen sharing and screenshots.", "ok"),
            "blackout": ("This Windows version can only black the window out "
                         "(needs Windows 10 2004+ to hide it).", "warn"),
            "off": ("Capture protection is OFF (config.json → capture_protection). "
                    "Others CAN see this window.", "warn"),
            "failed": ("Capture protection failed. Others CAN see this window.", "bad"),
            "pending": ("Checking…", "muted"),
        }[self.protection]
        h.insert("end", f"Invisipal {__version__}\n", "title")
        h.insert("end", status_text[0] + "\n", status_text[1])

        h.insert("end", "Global hotkeys (work without focus)\n", "title")
        failed = set(self.hotkey_thread.failed) if self.hotkey_thread else set()
        for hk in self.hotkey_list:
            h.insert("end", hk.text + "	", "bad" if hk.text in failed else "key")
            h.insert("end", ACTION_LABELS.get(hk.action, hk.action))
            h.insert("end", "   (in use by another app)\n" if hk.text in failed else "\n", "bad")
        for problem in self.hotkey_errors:
            h.insert("end", f"config error: {problem}\n", "bad")
        for warning in self.hotkey_warnings:
            h.insert("end", f"⚠ {warning}\n", "warn")

        h.insert("end", "When this window has focus\n", "title")
        for keys, label in LOCAL_KEYS:
            h.insert("end", keys + "	", "key")
            h.insert("end", label + "\n")

        h.insert("end", "Files\n", "title")
        h.insert("end", f"Guides:  {self.library.folder}\nConfig:  {self.cfg.path}\n", "muted")
        h.insert("end", "Mouse: drag the header to move, ◢ to resize, double-click the timer to reset.\n", "muted")
        h.configure(state="disabled")

    # ---------------------------------------------------------------- timer
    def toggle_timer(self) -> None:
        if self.timer_started is None:
            self.timer_started = time.monotonic()
            self.toast("Timer started")
        else:
            self.timer_elapsed += time.monotonic() - self.timer_started
            self.timer_started = None
            self.toast("Timer paused")
        self._render_timer()

    def reset_timer(self) -> None:
        self.timer_started = None
        self.timer_elapsed = 0.0
        self._render_timer()
        self.toast("Timer reset")

    def _render_timer(self) -> None:
        elapsed = self.timer_elapsed + (time.monotonic() - self.timer_started if self.timer_started else 0)
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        text = f"{hours}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"
        self.timer_label.config(text=text)
        self._set_fg(self.timer_label, self.theme["accent"] if self.timer_started else self.theme["muted"])

    def _tick_timer(self) -> None:
        if self.timer_started is not None:
            self._render_timer()
        self.root.after(500, self._tick_timer)

    # ----------------------------------------------------- move / resize / save
    def _drag_start(self, event) -> None:
        x, y = (win32.window_rect(self.hwnd)[:2] if self.hwnd
                else (self.root.winfo_x(), self.root.winfo_y()))
        self._drag = (event.x_root - x, event.y_root - y)

    def _drag_move(self, event) -> None:
        dx, dy = self._drag
        self.root.geometry(f"+{event.x_root - dx}+{event.y_root - dy}")

    def _resize_start(self, event) -> None:
        self._resize = (event.x_root, event.y_root, self.root.winfo_width(), self.root.winfo_height())

    def _resize_move(self, event) -> None:
        x0, y0, w0, h0 = self._resize
        w = max(MIN_W, w0 + event.x_root - x0)
        h = max(MIN_H, h0 + event.y_root - y0)
        self.root.geometry(f"{w}x{h}")

    def _store_geometry(self) -> None:
        # Tk's winfo_x/y are off by the (absent) frame on borderless windows.
        if self.visible and self.hwnd and self.root.winfo_exists():
            x, y, w, h = win32.window_rect(self.hwnd)
            self.cfg["x"], self.cfg["y"], self.cfg["width"], self.cfg["height"] = x, y, w, h

    def _schedule_save(self) -> None:
        if self._save_job:
            self.root.after_cancel(self._save_job)
        self._save_job = self.root.after(800, self._save_now)

    def _save_now(self) -> None:
        self._save_job = None
        self._store_geometry()
        self._remember_position()
        try:
            self.cfg.save()
        except OSError as exc:
            self.toast(f"Could not save config: {exc}", "danger", 4000)
