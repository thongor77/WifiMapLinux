from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QLabel, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QVBoxLayout, QWidget,
)
from sqlmodel import select

from ..models.access_point import AccessPoint
from ..models.database import get_session
from ..models.floor import Floor
from ..services.i18n import tr
from .dialogs.ap_dialog import APDialog

_ROLE = Qt.ItemDataRole.UserRole


def _band(freq_mhz: float) -> str:
    if freq_mhz < 3000:
        return "2.4 GHz"
    if freq_mhz < 6000:
        return "5 GHz"
    return "6 GHz"


class APPanel(QWidget):
    ap_deleted            = Signal(int)   # floor_id
    ap_edited             = Signal(int)   # floor_id
    ap_highlight_requested = Signal(int)  # ap_id  → start blink
    ap_unhighlight_requested = Signal()   # → stop blink
    ap_move_requested     = Signal(int)   # ap_id  → enter move mode

    def __init__(self, parent=None):
        super().__init__(parent)
        self._floor_id: int | None = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        title = QLabel(tr("panel_aps_title"))
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        self._floor_lbl = QLabel("—")
        self._floor_lbl.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self._floor_lbl)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.itemSelectionChanged.connect(self._on_selection)
        self._list.itemDoubleClicked.connect(self._on_edit)
        layout.addWidget(self._list)

        self._btn_edit   = QPushButton(tr("btn_edit"))
        self._btn_move   = QPushButton(tr("btn_move"))
        self._btn_delete = QPushButton(tr("btn_delete_ap"))
        for btn in (self._btn_edit, self._btn_move, self._btn_delete):
            btn.setEnabled(False)
        self._btn_delete.setStyleSheet("color: #c0392b;")

        self._btn_edit.clicked.connect(self._on_edit)
        self._btn_move.clicked.connect(self._on_move)
        self._btn_delete.clicked.connect(self._on_delete)

        layout.addWidget(self._btn_edit)
        layout.addWidget(self._btn_move)
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
        for btn in (self._btn_edit, self._btn_move, self._btn_delete):
            btn.setEnabled(False)

    # ── Internals ─────────────────────────────────────────────────────────

    def _refresh(self):
        selected_id = self._selected_ap_id()
        self._list.clear()
        if self._floor_id is None:
            return
        with get_session() as session:
            aps = session.exec(
                select(AccessPoint).where(AccessPoint.floor_id == self._floor_id)
            ).all()
            for ap in aps:
                text = f"📶  {ap.label}  ·  {ap.tx_power_dbm:.0f} dBm  ·  {_band(ap.frequency_mhz)}"
                item = QListWidgetItem(text)
                item.setData(_ROLE, ap.id)
                self._list.addItem(item)
                if ap.id == selected_id:
                    self._list.setCurrentItem(item)
        self._on_selection()

    def _selected_ap_id(self) -> int | None:
        items = self._list.selectedItems()
        return items[0].data(_ROLE) if items else None

    def _on_selection(self):
        has = bool(self._list.selectedItems())
        for btn in (self._btn_edit, self._btn_move, self._btn_delete):
            btn.setEnabled(has)
        if has:
            self.ap_highlight_requested.emit(self._selected_ap_id())
        else:
            self.ap_unhighlight_requested.emit()

    def _on_edit(self, *_):
        ap_id = self._selected_ap_id()
        if ap_id is None:
            return
        with get_session() as session:
            ap = session.get(AccessPoint, ap_id)
            if not ap:
                return
            label, tx, freq = ap.label, ap.tx_power_dbm, ap.frequency_mhz
            floor = session.get(Floor, ap.floor_id)
            building_id = floor.building_id if floor else None

        while True:
            dialog = APDialog(label=label, tx=tx, freq_mhz=freq, parent=self)
            if not dialog.exec():
                return
            new_label, new_tx, new_freq = dialog.get_data()
            if building_id is not None and self._ap_name_taken(
                new_label, building_id, exclude_ap_id=ap_id
            ):
                QMessageBox.warning(
                    self, tr("dlg_ap_name_taken_title"),
                    tr("dlg_ap_name_taken_msg", label=new_label),
                )
                label = new_label
                continue
            break

        with get_session() as session:
            ap = session.get(AccessPoint, ap_id)
            ap.label = new_label
            ap.tx_power_dbm = new_tx
            ap.frequency_mhz = new_freq
            session.add(ap)
            session.commit()
        self._refresh()
        self.ap_edited.emit(self._floor_id)

    def _ap_name_taken(
        self, name: str, building_id: int, exclude_ap_id: int | None = None
    ) -> bool:
        with get_session() as session:
            floor_ids = [
                f.id for f in session.exec(
                    select(Floor).where(Floor.building_id == building_id)
                ).all()
            ]
            q = select(AccessPoint).where(
                AccessPoint.floor_id.in_(floor_ids),
                AccessPoint.label == name,
            )
            if exclude_ap_id is not None:
                q = q.where(AccessPoint.id != exclude_ap_id)
            return session.exec(q).first() is not None

    def _on_move(self):
        ap_id = self._selected_ap_id()
        if ap_id is not None:
            self.ap_move_requested.emit(ap_id)

    def _on_delete(self):
        ap_id = self._selected_ap_id()
        if ap_id is None:
            return
        with get_session() as session:
            ap = session.get(AccessPoint, ap_id)
            label = ap.label if ap else "AP"
        reply = QMessageBox.question(
            self, tr("dlg_delete_ap_title"),
            tr("dlg_delete_ap_msg", label=label),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        with get_session() as session:
            ap = session.get(AccessPoint, ap_id)
            if ap:
                session.delete(ap)
                session.commit()
        self._refresh()
        self.ap_deleted.emit(self._floor_id)
