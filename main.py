import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.models.database import init_db
from app.ui.main_window import MainWindow


def main():
    init_db(Path(__file__).parent / "data")
    app = QApplication(sys.argv)
    app.setApplicationName("WifiMapLinux")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
