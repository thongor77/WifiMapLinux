from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit,
)

from ...services.i18n import tr

_FREQ_KEYS = ["freq_24ghz", "freq_5ghz", "freq_6ghz"]
_FREQ_VALUES = [2437.0, 5180.0, 5955.0]


class APDialog(QDialog):
    def __init__(
        self,
        label: str = "AP",
        tx: float = 20.0,
        freq_mhz: float = 2437.0,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_ap_title"))
        self.setMinimumWidth(320)
        layout = QFormLayout(self)

        self._label = QLineEdit(label)
        layout.addRow(tr("lbl_name"), self._label)

        self._tx = QDoubleSpinBox()
        self._tx.setRange(0.0, 30.0)
        self._tx.setValue(tx)
        self._tx.setSingleStep(1.0)
        self._tx.setSuffix(" dBm")
        self._tx.setToolTip(tr("tooltip_tx_power"))
        layout.addRow(tr("lbl_tx_power"), self._tx)

        self._freq = QComboBox()
        for key in _FREQ_KEYS:
            self._freq.addItem(tr(key))
        best = min(range(len(_FREQ_VALUES)), key=lambda i: abs(_FREQ_VALUES[i] - freq_mhz))
        self._freq.setCurrentIndex(best)
        layout.addRow(tr("lbl_wifi_band"), self._freq)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> tuple[str, float, float]:
        label = self._label.text().strip() or "AP"
        tx = self._tx.value()
        freq = _FREQ_VALUES[self._freq.currentIndex()]
        return label, tx, freq
