from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QFormLayout, QHeaderView, QLabel,
    QLineEdit, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from ...services.i18n import tr
from ...services.scanner import WifiNetwork


def _signal_color(dbm: int) -> str:
    if dbm >= -65:
        return "#2ecc71"
    if dbm >= -80:
        return "#f39c12"
    return "#e74c3c"


class ScanDialog(QDialog):
    def __init__(self, networks: list[WifiNetwork], parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_scan_title"))
        self.setMinimumSize(620, 380)
        self._networks = networks

        layout = QVBoxLayout(self)

        count = len(networks)
        summary = QLabel(tr("scan_summary", n=count))
        summary.setStyleSheet("font-weight: bold;")
        layout.addWidget(summary)

        self._table = QTableWidget(count, 5)
        self._table.setHorizontalHeaderLabels([
            tr("col_ssid"), tr("col_bssid"), tr("col_signal"),
            tr("col_channel"), tr("col_freq"),
        ])
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.verticalHeader().setVisible(False)

        for row, net in enumerate(sorted(networks, key=lambda n: -n.signal_dbm)):
            color = _signal_color(net.signal_dbm)
            for col, value in enumerate([net.ssid, net.bssid, str(net.signal_dbm),
                                          str(net.channel), str(net.frequency_mhz)]):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 2:
                    item.setForeground(Qt.GlobalColor.white)
                    item.setBackground(__import__("PySide6.QtGui", fromlist=["QColor"]).QColor(color))
                self._table.setItem(row, col, item)

        layout.addWidget(self._table)

        form = QFormLayout()
        self._label_edit = QLineEdit()
        self._label_edit.setPlaceholderText(tr("ph_scan_label"))
        form.addRow(tr("lbl_scan_label"), self._label_edit)
        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.button(QDialogButtonBox.StandardButton.Save).setText(tr("btn_save"))
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        if not networks:
            buttons.button(QDialogButtonBox.StandardButton.Save).setEnabled(False)

    def get_label(self) -> str | None:
        text = self._label_edit.text().strip()
        return text or None
