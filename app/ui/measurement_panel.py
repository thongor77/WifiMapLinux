from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)
from sqlmodel import select

from ..models.database import get_session
from ..models.measurement import MeasurementPoint, MeasurementScan
from ..services.i18n import tr

_ROLE = Qt.ItemDataRole.UserRole


class MeasurementPanel(QWidget):
    """Lists measurement points recorded on the current floor."""

    measurement_deleted = Signal(int)    # floor_id
    measurement_selected = Signal(float, float)  # x_px, y_px — highlight on plan

    def __init__(self, parent=None):
        super().__init__(parent)
        self._floor_id: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        title = QLabel(tr("panel_measurements_title"))
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        self._floor_lbl = QLabel("—")
        self._floor_lbl.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self._floor_lbl)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.setToolTip(tr("tooltip_meas_jump"))
        self._list.itemSelectionChanged.connect(self._on_selection)
        self._list.itemDoubleClicked.connect(self._on_jump)
        layout.addWidget(self._list)

        self._btn_delete = QPushButton(tr("btn_delete_measurement"))
        self._btn_delete.setEnabled(False)
        self._btn_delete.setStyleSheet("color: #c0392b;")
        self._btn_delete.clicked.connect(self._on_delete)
        layout.addWidget(self._btn_delete)

    # ── Public API ────────────────────────────────────────────────────────

    def load_floor(self, floor_id: int, floor_label: str = ""):
        self._floor_id = floor_id
        self._floor_lbl.setText(floor_label or "—")
        self._refresh()

    def refresh(self):
        self._refresh()

    def clear(self):
        self._floor_id = None
        self._floor_lbl.setText("—")
        self._list.clear()
        self._btn_delete.setEnabled(False)

    # ── Internals ─────────────────────────────────────────────────────────

    def _refresh(self):
        self._list.clear()
        if self._floor_id is None:
            return
        with get_session() as session:
            points = session.exec(
                select(MeasurementPoint)
                .where(MeasurementPoint.floor_id == self._floor_id)
                .order_by(MeasurementPoint.created_at)
            ).all()
            for idx, pt in enumerate(points, start=1):
                scans = session.exec(
                    select(MeasurementScan)
                    .where(MeasurementScan.measurement_point_id == pt.id)
                ).all()
                best = max((s.signal_dbm for s in scans), default=None)
                n_net = len(scans)
                display_label = pt.label or tr("measurement_point_label", n=idx)
                signal_str = f"{best} dBm" if best is not None else "—"
                text = f"📍  {display_label}  ·  {signal_str}  ·  {n_net} réseau{'x' if n_net > 1 else ''}"
                item = QListWidgetItem(text)
                item.setData(_ROLE, (pt.id, pt.x_px, pt.y_px))
                self._list.addItem(item)
        self._btn_delete.setEnabled(False)

    def _selected(self):
        items = self._list.selectedItems()
        return items[0].data(_ROLE) if items else None

    def _on_selection(self):
        data = self._selected()
        self._btn_delete.setEnabled(data is not None)

    def _on_jump(self, _item):
        data = self._selected()
        if data:
            _, x, y = data
            self.measurement_selected.emit(x, y)

    def _on_delete(self):
        data = self._selected()
        if data is None:
            return
        pt_id, _, _ = data
        reply = QMessageBox.question(
            self, tr("dlg_delete_meas_title"),
            tr("dlg_delete_meas_msg"),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        with get_session() as session:
            pt = session.get(MeasurementPoint, pt_id)
            if pt:
                for scan in session.exec(
                    select(MeasurementScan)
                    .where(MeasurementScan.measurement_point_id == pt_id)
                ).all():
                    session.delete(scan)
                session.delete(pt)
                session.commit()
        floor_id = self._floor_id
        self._refresh()
        if floor_id is not None:
            self.measurement_deleted.emit(floor_id)
