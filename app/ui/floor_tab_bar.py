from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QTabBar, QWidget


class FloorTabBar(QWidget):
    """Horizontal tab bar showing all floors of the active building."""

    floor_selected = Signal(int)  # floor_id

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 0, 4, 0)

        self._tab_bar = QTabBar()
        self._tab_bar.setExpanding(False)
        self._floor_ids: list[int] = []
        self._tab_bar.currentChanged.connect(self._on_changed)
        layout.addWidget(self._tab_bar)
        layout.addStretch()

        self.setFixedHeight(32)
        self.hide()

    def populate(self, floors: list[tuple[int, str]]):
        """Replace all tabs. floors = [(floor_id, label), ...] ordered by index asc."""
        self._tab_bar.blockSignals(True)
        while self._tab_bar.count():
            self._tab_bar.removeTab(0)
        self._floor_ids = []
        for fid, label in floors:
            self._tab_bar.addTab(label)
            self._floor_ids.append(fid)
        self._tab_bar.blockSignals(False)
        self.setVisible(bool(floors))

    def set_active(self, floor_id: int):
        """Highlight the tab for the given floor without emitting floor_selected."""
        if floor_id in self._floor_ids:
            self._tab_bar.blockSignals(True)
            self._tab_bar.setCurrentIndex(self._floor_ids.index(floor_id))
            self._tab_bar.blockSignals(False)

    def _on_changed(self, idx: int):
        if 0 <= idx < len(self._floor_ids):
            self.floor_selected.emit(self._floor_ids[idx])
