from PySide6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit

from ...services.i18n import tr


class BuildingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("dlg_new_building_title"))
        self.setMinimumWidth(320)

        layout = QFormLayout(self)
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(tr("ph_building_name"))
        self.address_edit = QLineEdit()
        self.address_edit.setPlaceholderText(tr("ph_optional"))
        layout.addRow(tr("lbl_name"), self.name_edit)
        layout.addRow(tr("lbl_address"), self.address_edit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_accept(self):
        if self.name_edit.text().strip():
            self.accept()

    def get_data(self) -> tuple[str, str | None]:
        name = self.name_edit.text().strip()
        address = self.address_edit.text().strip() or None
        return name, address
