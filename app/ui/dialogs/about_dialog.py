from __future__ import annotations

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout,
    QLabel, QPushButton, QVBoxLayout,
)

from ...services.i18n import tr
from ...__version__ import __version__

_GITHUB_URL = "https://github.com/thongor77/WifiMapLinux"


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about_title"))
        self.setFixedWidth(460)
        self.setModal(True)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(32, 28, 32, 20)
        root.setSpacing(0)

        # ── App name ──────────────────────────────────────────────────────
        name_lbl = QLabel("WifiMapLinux")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        name_lbl.setStyleSheet("font-size: 24px; font-weight: bold;")
        root.addWidget(name_lbl)

        ver_lbl = QLabel(tr("about_version", version=__version__))
        ver_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        ver_lbl.setStyleSheet("font-size: 12px; color: palette(mid); margin-bottom: 6px;")
        root.addWidget(ver_lbl)

        desc_lbl = QLabel(tr("about_description"))
        desc_lbl.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 13px; margin-bottom: 18px;")
        root.addWidget(desc_lbl)

        # ── Separator ─────────────────────────────────────────────────────
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setStyleSheet("margin-bottom: 14px;")
        root.addWidget(sep)

        # ── Tech section ──────────────────────────────────────────────────
        tech_title = QLabel(tr("about_tech_title"))
        tech_title.setStyleSheet("font-weight: bold; font-size: 12px;")
        root.addWidget(tech_title)

        tech_body = QLabel(tr("about_tech_body"))
        tech_body.setWordWrap(True)
        tech_body.setStyleSheet("font-size: 12px; color: palette(text); margin-bottom: 16px;")
        root.addWidget(tech_body)

        # ── GitHub link ───────────────────────────────────────────────────
        gh_row = QHBoxLayout()
        gh_row.setContentsMargins(0, 0, 0, 0)
        gh_lbl = QLabel("GitHub :")
        gh_lbl.setStyleSheet("font-size: 12px;")
        gh_row.addWidget(gh_lbl)

        btn_gh = QPushButton(tr("about_github_btn"))
        btn_gh.setFlat(True)
        btn_gh.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_gh.setStyleSheet(
            "color: palette(link); text-decoration: underline; font-size: 12px; text-align: left;"
        )
        btn_gh.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(_GITHUB_URL)))
        gh_row.addWidget(btn_gh)
        gh_row.addStretch(1)
        root.addLayout(gh_row)

        root.addSpacing(20)

        # ── OK button ─────────────────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        root.addWidget(buttons)
