from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit,
)

# ADR-004 — ITU-R P.1238 floor attenuation presets
_FLOOR_MATERIALS: list[tuple[str, float]] = [
    ("Béton (12 dB) — défaut", 12.0),
    ("Béton armé (18 dB)", 18.0),
    ("Bois / plancher léger (5 dB)", 5.0),
]

_PRESETS: list[tuple[int, str]] = [
    (-1, "Cave / Sous-sol"),
    (0, "Rez-de-chaussée"),
    (1, "1er étage"),
    (2, "2e étage"),
    (3, "3e étage"),
]


class FloorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nouvel étage")
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        self.preset_combo = QComboBox()
        for index, label in _PRESETS:
            self.preset_combo.addItem(label, userData=index)
        self.preset_combo.currentIndexChanged.connect(self._sync_label)
        layout.addRow("Étage :", self.preset_combo)

        self.label_edit = QLineEdit()
        layout.addRow("Libellé :", self.label_edit)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1.5, 10.0)
        self.height_spin.setValue(2.5)
        self.height_spin.setSingleStep(0.1)
        self.height_spin.setDecimals(1)
        self.height_spin.setSuffix(" m")
        layout.addRow("Hauteur sous plafond :", self.height_spin)

        self.material_combo = QComboBox()
        for label, _ in _FLOOR_MATERIALS:
            self.material_combo.addItem(label)
        self.material_combo.setToolTip(
            "Atténuation de la dalle (ADR-004 — ITU-R P.1238)\n"
            "Utilisée par la simulation Wi-Fi inter-étages."
        )
        layout.addRow("Matériau dalle :", self.material_combo)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

        self._sync_label(0)

    def _sync_label(self, _idx: int):
        self.label_edit.setText(self.preset_combo.currentText())

    def get_data(self) -> tuple[int, str, float, float]:
        index: int = self.preset_combo.currentData()
        label = self.label_edit.text().strip() or self.preset_combo.currentText()
        height = self.height_spin.value()
        attenuation = _FLOOR_MATERIALS[self.material_combo.currentIndex()][1]
        return index, label, height, attenuation
