from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit,
)

_FREQ_OPTIONS: list[tuple[str, float]] = [
    ("2.4 GHz — ch 6 (2437 MHz)", 2437.0),
    ("5 GHz — ch 36 (5180 MHz)", 5180.0),
    ("6 GHz — ch 1 (5955 MHz)", 5955.0),
]


class APDialog(QDialog):
    def __init__(
        self,
        label: str = "AP",
        tx: float = 20.0,
        freq_mhz: float = 2437.0,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Point d'accès virtuel")
        self.setMinimumWidth(320)
        layout = QFormLayout(self)

        self._label = QLineEdit(label)
        layout.addRow("Nom :", self._label)

        self._tx = QDoubleSpinBox()
        self._tx.setRange(0.0, 30.0)
        self._tx.setValue(tx)
        self._tx.setSingleStep(1.0)
        self._tx.setSuffix(" dBm")
        self._tx.setToolTip("Puissance d'émission typique : 20 dBm (100 mW)")
        layout.addRow("Puissance TX :", self._tx)

        self._freq = QComboBox()
        for lbl, _ in _FREQ_OPTIONS:
            self._freq.addItem(lbl)
        # Pre-select the closest frequency option
        best = min(range(len(_FREQ_OPTIONS)), key=lambda i: abs(_FREQ_OPTIONS[i][1] - freq_mhz))
        self._freq.setCurrentIndex(best)
        layout.addRow("Bande Wi-Fi :", self._freq)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def get_data(self) -> tuple[str, float, float]:
        label = self._label.text().strip() or "AP"
        tx = self._tx.value()
        freq = _FREQ_OPTIONS[self._freq.currentIndex()][1]
        return label, tx, freq
