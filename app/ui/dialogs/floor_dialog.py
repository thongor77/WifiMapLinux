from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFormLayout, QLineEdit,
)

from ...services.i18n import tr

# ADR-004 — ITU-R P.1238 floor attenuation presets
_FLOOR_PRESET_INDICES = [-1, 0, 1, 2, 3]
_FLOOR_PRESET_KEYS = [
    "floor_preset_basement",
    "floor_preset_ground",
    "floor_preset_1",
    "floor_preset_2",
    "floor_preset_3",
]

_FLOOR_MATERIAL_KEYS = [
    "material_concrete",
    "material_reinforced",
    "material_wood",
]
_FLOOR_MATERIAL_VALUES = [12.0, 18.0, 5.0]


class FloorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_new_floor_title"))
        self.setMinimumWidth(320)

        layout = QFormLayout(self)

        self.preset_combo = QComboBox()
        for idx, key in zip(_FLOOR_PRESET_INDICES, _FLOOR_PRESET_KEYS):
            self.preset_combo.addItem(tr(key), userData=idx)
        self.preset_combo.currentIndexChanged.connect(self._sync_label)
        layout.addRow(tr("lbl_floor"), self.preset_combo)

        self.label_edit = QLineEdit()
        layout.addRow(tr("lbl_label"), self.label_edit)

        self.height_spin = QDoubleSpinBox()
        self.height_spin.setRange(1.5, 10.0)
        self.height_spin.setValue(2.5)
        self.height_spin.setSingleStep(0.1)
        self.height_spin.setDecimals(1)
        self.height_spin.setSuffix(" m")
        layout.addRow(tr("lbl_ceiling_height"), self.height_spin)

        self.material_combo = QComboBox()
        for key in _FLOOR_MATERIAL_KEYS:
            self.material_combo.addItem(tr(key))
        self.material_combo.setToolTip(tr("tooltip_slab_material"))
        layout.addRow(tr("lbl_slab_material"), self.material_combo)

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
        attenuation = _FLOOR_MATERIAL_VALUES[self.material_combo.currentIndex()]
        return index, label, height, attenuation
