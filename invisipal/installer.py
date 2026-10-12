"""Setup for the Python version: copy Invisipal to a per-user folder and add shortcuts.

Run by double-clicking ``Install Invisipal.pyw``. It needs no admin rights and
no extra packages. The app is copied to ``%LOCALAPPDATA%\\Invisipal\\app`` and
started with ``pythonw.exe``, which is signed by the Python Software Foundation,
so it also works on PCs where Smart App Control blocks unsigned executables.
User data (guides, settings) stays in ``Documents\\Invisipal`` and is never touched.
"""

from __future__ import annotations

import ctypes
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__

SOURCE = Path(__file__).resolve().parent.parent  # folder that holds invisipal.pyw
SHORTCUT_PLACES = ("Programs", "Desktop", "Startup")  # .NET Environment.SpecialFolder names
MARKER = "install.json"
OLD_EXE_INSTALL = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Invisipal" / "Invisipal.exe"

# Shortcuts are created by PowerShell's WScript.Shell COM object: it resolves
# redirected folders (OneDrive Desktop, etc.) and needs no extra Python packages.
SHORTCUT_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject WScript.Shell
foreach ($place in $env:INV_PLACES.Split(',')) {
    if (-not $place) { continue }
    $dir = [Environment]::GetFolderPath($place)
    if (-not $dir) { continue }
    $link = Join-Path $dir 'Invisipal.lnk'
    if ($env:INV_ACTION -eq 'remove') {
        if (Test-Path -LiteralPath $link) { Remove-Item -LiteralPath $link -Force }
        continue
    }
    $s = $shell.CreateShortcut($link)
    $s.TargetPath = $env:INV_TARGET
    $s.Arguments = $env:INV_ARGS
    $s.WorkingDirectory = $env:INV_WORKDIR
    $s.IconLocation = $env:INV_ICON
    $s.Description = 'Private meeting notes hidden from screen sharing'
    $s.Save()
}
"""

TEXTS = {
    "en": {
        "title": "Invisipal setup",
        "intro": "Invisipal {version} will be installed for your user (no admin rights needed).",
        "where": "Program: {app}\nYour guides and settings: Documents\\Invisipal (never deleted)",
        "start_menu": "Start menu shortcut",
        "desktop": "Desktop shortcut",
        "startup": "Start Invisipal when I sign in to Windows",
        "install": "Install",
        "update": "Update",
        "uninstall": "Uninstall",
        "open": "Open Invisipal",
        "close": "Close",
        "done": "Done! Invisipal is in your Start menu.\nTip: press Ctrl+Alt+H to show or hide it.",
        "removed": "Invisipal was uninstalled. Your guides are still in Documents\\Invisipal.",
        "installed_version": "Installed version: {version}",
        "running": "Invisipal is running. Close it first (Ctrl+Alt+Q, or Ctrl+Alt+Shift+Q), then try again.",
        "old_exe": "Note: an Invisipal.exe installation was also found. Uninstall it from Settings → Apps "
                   "so you don't end up with two shortcuts.",
        "error": "Something went wrong:\n{error}",
        "store_python": "This Python comes from the Microsoft Store. If the shortcuts don't appear, "
                        "install Python from python.org and run this setup again.",
    },
    "es": {
        "title": "Instalar Invisipal",
        "intro": "Se va a instalar Invisipal {version} para tu usuario (no hace falta ser administrador).",
        "where": "Programa: {app}\nTus guías y configuración: Documentos\\Invisipal (nunca se borran)",
        "start_menu": "Acceso directo en el menú Inicio",
        "desktop": "Acceso directo en el escritorio",
        "startup": "Abrir Invisipal al iniciar sesión en Windows",
        "install": "Instalar",
        "update": "Actualizar",
        "uninstall": "Desinstalar",
        "open": "Abrir Invisipal",
        "close": "Cerrar",
        "done": "¡Listo! Invisipal está en tu menú Inicio.\nTip: Ctrl+Alt+H la muestra u oculta.",
        "removed": "Invisipal se desinstaló. Tus guías siguen en Documentos\\Invisipal.",
        "installed_version": "Versión instalada: {version}",
        "running": "Invisipal está abierto. Cerralo primero (Ctrl+Alt+Q o Ctrl+Alt+Shift+Q) y volvé a intentar.",
        "old_exe": "Nota: también hay una instalación de Invisipal.exe. Desinstalala desde Configuración → "
                   "Aplicaciones para no tener dos accesos directos.",
        "error": "Algo salió mal:\n{error}",
        "store_python": "Este Python es de la Microsoft Store. Si no aparecen los accesos directos, "
                        "instalá Python desde python.org y volvé a ejecutar este instalador.",
    },
}


def language() -> str:
    try:
        lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
    except (AttributeError, OSError):
        return "en"
    return "es" if lang_id & 0x3FF == 0x0A else "en"  # LANG_SPANISH, any country


def install_dir() -> Path:
    return Path(os.environ["LOCALAPPDATA"]) / "Invisipal" / "app"


def pythonw_path(executable: str | None = None) -> Path:
    """The windowless interpreter next to the running one (python.exe -> pythonw.exe)."""
    exe = Path(executable or sys.executable)
    candidate = exe.with_name("pythonw.exe")
    return candidate if candidate.exists() else exe


def is_store_python(executable: str | None = None) -> bool:
    return "WindowsApps" in str(executable or sys.executable)


def is_running() -> bool:
    """True if an Invisipal instance holds the single-instance event."""
    try:
        handle = ctypes.windll.kernel32.OpenEventW(0x00100000, False, "Local\\Invisipal.SingleInstance.v1")
    except (AttributeError, OSError):
        return False
    if handle:
        ctypes.windll.kernel32.CloseHandle(handle)
        return True
    return False


def installed_info(app: Path | None = None) -> dict | None:
    marker = (app or install_dir()) / MARKER
    try:
        return json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def copy_app(source: Path, app: Path) -> None:
    """Replace the program files in ``app`` with the ones from ``source``."""
    if source.resolve() == app.resolve():
        return  # setup was started from the installed copy itself
    package = app / "invisipal"
    if package.exists():
        shutil.rmtree(package)  # no stale modules from an older version
    app.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "invisipal", package, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for name in ("invisipal.pyw", "LICENSE", "README.md"):
        if (source / name).is_file():
            shutil.copy2(source / name, app / name)


def shortcut_env(app: Path, places: list[str], action: str = "create", pythonw: Path | None = None) -> dict:
    env = dict(os.environ)
    env.update(
        INV_ACTION=action,
        INV_PLACES=",".join(places),
        INV_TARGET=str(pythonw or pythonw_path()),
        INV_ARGS=f'"{app / "invisipal.pyw"}"',
        INV_WORKDIR=str(app),
        INV_ICON=str(app / "invisipal" / "assets" / "invisipal.ico"),
    )
    return env


def run_shortcut_script(env: dict) -> None:
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", SHORTCUT_SCRIPT],
        env=env, capture_output=True, text=True, creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "PowerShell could not create the shortcuts")


def install(places: list[str], source: Path = SOURCE, app: Path | None = None) -> Path:
    app = app or install_dir()
    copy_app(source, app)
    run_shortcut_script(shortcut_env(app, list(SHORTCUT_PLACES), action="remove"))  # drop unchecked ones
    run_shortcut_script(shortcut_env(app, places))
    (app / MARKER).write_text(json.dumps({"version": __version__, "shortcuts": places}, indent=2), encoding="utf-8")
    return app


def uninstall(app: Path | None = None) -> None:
    app = app or install_dir()
    run_shortcut_script(shortcut_env(app, list(SHORTCUT_PLACES), action="remove"))
    if (app / MARKER).exists():  # only delete a folder this setup created
        shutil.rmtree(app)


def launch(app: Path | None = None) -> None:
    app = app or install_dir()
    subprocess.Popen([str(pythonw_path()), str(app / "invisipal.pyw")], cwd=str(app),
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))


# --------------------------------------------------------------------------- UI
def main() -> int:
    import tkinter as tk
    import tkinter.font as tkfont

    t = TEXTS[language()]
    app = install_dir()
    info = installed_info(app)

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except (AttributeError, OSError):
        pass
    root = tk.Tk()
    root.title(t["title"])
    root.resizable(False, False)
    try:
        root.iconbitmap(default=str(SOURCE / "invisipal" / "assets" / "invisipal.ico"))
    except tk.TclError:
        pass
    bg, fg, muted, accent = "#14161b", "#e7e9ee", "#8a93a6", "#7aa2f7"
    root.configure(bg=bg, padx=24, pady=20)
    font = tkfont.Font(family="Segoe UI", size=10)
    bold = tkfont.Font(family="Segoe UI Semibold", size=14)

    try:
        logo = tk.PhotoImage(file=str(SOURCE / "invisipal" / "assets" / "header.png"))
        tk.Label(root, image=logo, bg=bg).pack(anchor="w")
    except tk.TclError:
        logo = None
    tk.Label(root, text=f"Invisipal {__version__}", font=bold, bg=bg, fg=fg).pack(anchor="w", pady=(4, 2))
    tk.Label(root, text=t["intro"].format(version=__version__), font=font, bg=bg, fg=fg,
             justify="left", wraplength=440).pack(anchor="w")
    tk.Label(root, text=t["where"].format(app=app), font=font, bg=bg, fg=muted,
             justify="left", wraplength=440).pack(anchor="w", pady=(6, 10))
    if info:
        tk.Label(root, text=t["installed_version"].format(version=info.get("version", "?")), font=font,
                 bg=bg, fg=accent).pack(anchor="w", pady=(0, 6))

    choices = {}
    defaults = info.get("shortcuts") if info else ["Programs", "Desktop"]
    for place, key in (("Programs", "start_menu"), ("Desktop", "desktop"), ("Startup", "startup")):
        var = tk.BooleanVar(value=place in defaults)
        tk.Checkbutton(root, text=t[key], variable=var, font=font, bg=bg, fg=fg, selectcolor=bg,
                       activebackground=bg, activeforeground=fg, anchor="w").pack(anchor="w")
        choices[place] = var

    notes = []
    if OLD_EXE_INSTALL.exists():
        notes.append(t["old_exe"])
    if is_store_python():
        notes.append(t["store_python"])
    status = tk.Label(root, text="\n\n".join(notes), font=font, bg=bg, fg=muted, justify="left", wraplength=440)
    status.pack(anchor="w", pady=(10, 0))

    buttons = tk.Frame(root, bg=bg)
    buttons.pack(anchor="e", pady=(14, 0), fill="x")

    def button(text, command, primary=False):
        return tk.Button(buttons, text=text, command=command, font=font, relief="flat", padx=14, pady=4,
                         bg=accent if primary else "#2a2f3a", fg="#0d1117" if primary else fg,
                         activebackground=fg, cursor="hand2")

    def finish(message, can_open):
        for child in buttons.winfo_children():
            child.destroy()
        status.config(text=message, fg=fg)
        if can_open:
            button(t["open"], lambda: (launch(app), root.destroy()), primary=True).pack(side="right")
        button(t["close"], root.destroy).pack(side="right", padx=(0, 8))

    def do_install():
        if is_running():
            status.config(text=t["running"], fg="#f2b45a")
            return
        try:
            install([place for place, var in choices.items() if var.get()], app=app)
        except Exception as exc:  # noqa: BLE001 - show any failure to the user
            status.config(text=t["error"].format(error=exc), fg="#f7768e")
            return
        finish(t["done"], can_open=True)

    def do_uninstall():
        if is_running():
            status.config(text=t["running"], fg="#f2b45a")
            return
        try:
            uninstall(app)
        except Exception as exc:  # noqa: BLE001
            status.config(text=t["error"].format(error=exc), fg="#f7768e")
            return
        finish(t["removed"], can_open=False)

    button(t["update"] if info else t["install"], do_install, primary=True).pack(side="right")
    if info:
        button(t["uninstall"], do_uninstall).pack(side="right", padx=(0, 8))

    root.logo = logo
    root.mainloop()
    return 0
