import numpy as np
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QImage, QPainter, QPixmap
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QPushButton, QSlider, QWidget,
)

from ..services.i18n import tr
from ..services.interpolation import _STOPS, grid_to_rgba


class _LegendWidget(QWidget):
    """Horizontal gradient bar −95 → −40 dBm with tick labels."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 28)
        self._pixmap = self._build_pixmap()

    def _build_pixmap(self) -> QPixmap:
        W, H = 200, 12
        row = np.linspace(_STOPS[0, 0], _STOPS[-1, 0], W).reshape(1, W)
        rgba = grid_to_rgba(row)            # (1, W, 4)
        # Force alpha=220 for the legend (it's on a solid background)
        rgba[:, :, 3] = np.where(rgba[:, :, 3] > 0, 220, 0)
        img = QImage(rgba.tobytes(), W, H, 4 * W, QImage.Format.Format_RGBA8888)
        return QPixmap.fromImage(img.scaled(W, H))

    def paintEvent(self, _event):
        p = QPainter(self)
        p.drawPixmap(10, 2, self._pixmap)
        p.setPen(Qt.GlobalColor.white)
        font = p.font()
        font.setPointSize(7)
        p.setFont(font)
        labels = [("-95", 10), ("-75", 60), ("-55", 120), ("-40", 180)]
        for text, x in labels:
            p.drawText(x, 26, text)


class HeatmapControls(QWidget):
    toggled = Signal(bool)
    sim_toggled = Signal(bool)
    ssid_changed = Signal(str)
    opacity_changed = Signal(int)   # 0-100
    section_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(38)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(10)

        self._check = QCheckBox(tr("chk_heatmap"))
        self._check.toggled.connect(self.toggled)
        layout.addWidget(self._check)

        self._sim_check = QCheckBox(tr("chk_simulation"))
        self._sim_check.setToolTip(tr("tooltip_simulation"))
        self._sim_check.toggled.connect(self.sim_toggled)
        layout.addWidget(self._sim_check)

        layout.addWidget(QLabel(tr("lbl_network")))
        self._ssid_combo = QComboBox()
        self._ssid_combo.setFixedWidth(190)
        self._ssid_combo.currentIndexChanged.connect(self._on_ssid_changed)
        layout.addWidget(self._ssid_combo)

        layout.addWidget(QLabel(tr("lbl_opacity")))
        self._opacity = QSlider(Qt.Orientation.Horizontal)
        self._opacity.setRange(10, 100)
        self._opacity.setValue(70)
        self._opacity.setFixedWidth(100)
        self._opacity.valueChanged.connect(self.opacity_changed)
        layout.addWidget(self._opacity)

        layout.addWidget(_LegendWidget())

        sep = QLabel("|")
        sep.setStyleSheet("color: #555555;")
        layout.addWidget(sep)

        self._section_btn = QPushButton(tr("btn_section"))
        self._section_btn.setFixedHeight(24)
        self._section_btn.setToolTip(tr("tooltip_section"))
        self._section_btn.clicked.connect(self.section_requested)
        layout.addWidget(self._section_btn)

        layout.addStretch()

    def populate_ssids(self, ssids: list[str]):
        self._ssid_combo.blockSignals(True)
        self._ssid_combo.clear()
        self._ssid_combo.addItem(tr("combo_best_signal"), userData="")
        for ssid in sorted(set(ssids)):
            if ssid:
                self._ssid_combo.addItem(ssid, userData=ssid)
        self._ssid_combo.blockSignals(False)

    def _on_ssid_changed(self, _idx: int):
        self.ssid_changed.emit(self._ssid_combo.currentData() or "")

    def selected_ssid(self) -> str:
        return self._ssid_combo.currentData() or ""

    def opacity(self) -> float:
        return self._opacity.value() / 100.0

    def is_active(self) -> bool:
        return self._check.isChecked()

    def heatmap_is_active(self) -> bool:
        return self._check.isChecked()

    def sim_is_active(self) -> bool:
        return self._sim_check.isChecked()
