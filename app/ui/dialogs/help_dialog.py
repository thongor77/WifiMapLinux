from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFrame, QHBoxLayout,
    QLabel, QListWidget, QListWidgetItem, QScrollArea,
    QSizePolicy, QVBoxLayout, QWidget,
)

from ...services.help_content import get_help, get_topics
from ...services.i18n import tr

_ROLE = Qt.ItemDataRole.UserRole


class HelpDialog(QDialog):
    def __init__(self, parent=None, initial_topic: str | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("help_title"))
        self.resize(780, 520)
        self.setModal(True)
        self._build_ui()
        self._populate_topics()
        first = initial_topic or get_topics()[0]
        self._select_topic(first)

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 12)
        root.setSpacing(0)

        # ── Body (topic list + content) ───────────────────────────────────
        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)

        # Left: topic list
        self._topic_list = QListWidget()
        self._topic_list.setFixedWidth(175)
        self._topic_list.setStyleSheet(
            "QListWidget { border: none; border-right: 1px solid palette(mid); "
            "padding: 8px 0; font-size: 13px; }"
            "QListWidget::item { padding: 8px 14px; }"
            "QListWidget::item:selected { background: palette(highlight); color: palette(highlighted-text); }"
        )
        self._topic_list.currentItemChanged.connect(self._on_topic_changed)
        body.addWidget(self._topic_list)

        # Right: scrollable content
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(28, 20, 28, 28)
        self._content_layout.setSpacing(0)
        self._content_layout.addStretch(1)

        self._scroll.setWidget(self._content_widget)
        body.addWidget(self._scroll, 1)

        root.addLayout(body, 1)

        # ── Close button ──────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(12, 0, 12, 0)
        btn_row.addStretch(1)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        btn_row.addWidget(buttons)
        root.addLayout(btn_row)

    def _populate_topics(self) -> None:
        topic_label_keys = {
            "project":    "help_topic_project",
            "calibrate":  "help_topic_calibrate",
            "measure":    "help_topic_measure",
            "heatmap":    "help_topic_heatmap",
            "simulation": "help_topic_simulation",
            "section":    "help_topic_section",
            "alignment":  "help_topic_alignment",
            "export":     "help_topic_export",
        }
        for key in get_topics():
            label = tr(topic_label_keys.get(key, key))
            item = QListWidgetItem(label)
            item.setData(_ROLE, key)
            self._topic_list.addItem(item)

    def _select_topic(self, key: str) -> None:
        for i in range(self._topic_list.count()):
            item = self._topic_list.item(i)
            if item.data(_ROLE) == key:
                self._topic_list.setCurrentItem(item)
                return
        if self._topic_list.count():
            self._topic_list.setCurrentRow(0)

    def _on_topic_changed(self, current: QListWidgetItem | None, _prev) -> None:
        if current is None:
            return
        self._load_content(current.data(_ROLE))

    def _load_content(self, topic_key: str) -> None:
        # Clear previous content (keep trailing stretch)
        while self._content_layout.count() > 1:
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        data = get_help(topic_key)
        if not data:
            lbl = QLabel(tr("help_no_content"))
            lbl.setStyleSheet("color: palette(mid); font-size: 13px;")
            self._content_layout.insertWidget(0, lbl)
            return

        idx = 0

        # ── Description ───────────────────────────────────────────────────
        self._content_layout.insertWidget(idx, self._section_title(tr("help_section_desc"))); idx += 1
        desc = QLabel(data["desc"])
        desc.setWordWrap(True)
        desc.setStyleSheet("font-size: 13px; margin-bottom: 18px;")
        desc.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self._content_layout.insertWidget(idx, desc); idx += 1

        # ── Steps ─────────────────────────────────────────────────────────
        if data.get("steps"):
            self._content_layout.insertWidget(idx, self._section_title(tr("help_section_steps"))); idx += 1
            for n, step in enumerate(data["steps"], start=1):
                row, lbl = self._bullet_row(f"{n}.", step)
                lbl.setStyleSheet("font-size: 13px;")
                self._content_layout.insertWidget(idx, row); idx += 1
            spacer = QWidget(); spacer.setFixedHeight(12)
            self._content_layout.insertWidget(idx, spacer); idx += 1

        # ── Tips ──────────────────────────────────────────────────────────
        if data.get("tips"):
            self._content_layout.insertWidget(idx, self._section_title(tr("help_section_tips"))); idx += 1
            for tip in data["tips"]:
                row, lbl = self._bullet_row("→", tip)
                lbl.setStyleSheet("font-size: 13px; color: palette(text);")
                self._content_layout.insertWidget(idx, row); idx += 1

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _section_title(text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 6px;")
        return lbl

    @staticmethod
    def _bullet_row(prefix: str, text: str) -> tuple[QWidget, QLabel]:
        row = QWidget()
        row.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Minimum)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(8)

        pfx = QLabel(prefix)
        pfx.setFixedWidth(20)
        pfx.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        pfx.setStyleSheet("font-size: 13px; color: palette(link); padding-top: 1px;")

        body = QLabel(text)
        body.setWordWrap(True)
        body.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)

        layout.addWidget(pfx)
        layout.addWidget(body, 1)
        return row, body
