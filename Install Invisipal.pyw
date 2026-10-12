"""Double-click me to install Invisipal: Start menu and desktop shortcuts, no admin rights.

Needs Python 3.10+ from https://www.python.org/downloads/
"""

import sys

if sys.version_info < (3, 10):
    import ctypes

    ctypes.windll.user32.MessageBoxW(
        None,
        "Invisipal needs Python 3.10 or newer.\n\nDownload it from https://www.python.org/downloads/",
        "Invisipal",
        0x10,
    )
    raise SystemExit(1)

from invisipal.installer import main  # noqa: E402

raise SystemExit(main())
