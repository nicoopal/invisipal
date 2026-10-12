"""Build dist/Invisipal.zip: the Python version, ready to unzip and install.

Contents (inside an "Invisipal" folder): the invisipal package, invisipal.pyw,
"Install Invisipal.pyw", LICENSE, README.md and a short bilingual start guide.
Usage: python scripts/make_python_zip.py
"""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = ["invisipal.pyw", "Install Invisipal.pyw", "LICENSE", "README.md"]

START_HERE = r"""INVISIPAL - START HERE / EMPEZÁ ACÁ
====================================

ENGLISH
1. You need Python 3.10 or newer: https://www.python.org/downloads/
   (if you don't have it, install it and come back).
2. Double-click "Install Invisipal.pyw".
3. Click Install. Invisipal is now in your Start menu (and on your desktop).

Your guides and settings live in Documents\Invisipal.
To update: download the new Invisipal.zip and run "Install Invisipal.pyw" again.
To uninstall: run "Install Invisipal.pyw" and click Uninstall.

ESPAÑOL
1. Necesitás Python 3.10 o más nuevo: https://www.python.org/downloads/
   (si no lo tenés, instalalo y volvé).
2. Hacé doble clic en "Install Invisipal.pyw".
3. Tocá Instalar. Invisipal ya está en tu menú Inicio (y en el escritorio).

Tus guías y configuración quedan en Documentos\Invisipal.
Para actualizar: bajá el nuevo Invisipal.zip y volvé a ejecutar "Install Invisipal.pyw".
Para desinstalar: ejecutá "Install Invisipal.pyw" y tocá Desinstalar.

More / Más: https://github.com/nicoopal/invisipal
"""


def build(out: Path = ROOT / "dist" / "Invisipal.zip") -> Path:
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted((ROOT / "invisipal").rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
                zf.write(path, Path("Invisipal") / path.relative_to(ROOT))
        for name in FILES:
            zf.write(ROOT / name, Path("Invisipal") / name)
        zf.writestr("Invisipal/START HERE - EMPEZA ACA.txt", START_HERE.replace("\n", "\r\n"))
    return out


if __name__ == "__main__":
    path = build(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "dist" / "Invisipal.zip")
    print(f"{path} ({path.stat().st_size / 1024:.0f} KB)")
