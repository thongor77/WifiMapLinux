"""Entry point for installed package (`wifimaplinux` command).

Development: use main.py at the repo root instead (./data/ for database).
Installed:   database lives in ~/.local/share/wifimaplinux/
"""
from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .models.database import init_db
from .ui.main_window import MainWindow

_DATA_DIR = Path.home() / ".local" / "share" / "wifimaplinux"


def main() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)
    init_db(_DATA_DIR)
    app = QApplication(sys.argv)
    app.setApplicationName("WifiMapLinux")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
