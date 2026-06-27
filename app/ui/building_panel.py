from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QLabel, QMessageBox, QPushButton, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)
from sqlmodel import select

from ..models.access_point import AccessPoint
from ..models.building import Building
from ..models.database import get_session
from ..models.floor import Floor, FloorPlan
from ..models.measurement import MeasurementPoint, MeasurementScan
from ..services.i18n import tr
from .dialogs.building_dialog import BuildingDialog
from .dialogs.floor_dialog import FloorDialog

_ROLE = Qt.ItemDataRole.UserRole


class BuildingPanel(QWidget):
    building_selected = Signal(int)
    floor_selected = Signal(int)
    import_plan_requested = Signal(int)
    calibrate_requested = Signal(int)
    measure_requested = Signal(int)
    alignment_requested = Signal(int)
    place_ap_requested = Signal(int)
    building_deleted = Signal()
    floor_deleted = Signal()
    data_changed = Signal()       # creation / calibration events

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_building_id: int | None = None
        self._current_floor_id: int | None = None
        self._setup_ui()
        self.refresh()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        title = QLabel(tr("panel_buildings_title"))
        title.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(title)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

        self.btn_new_building = QPushButton(tr("btn_new_building"))
        self.btn_new_floor    = QPushButton(tr("btn_new_floor"))
        self.btn_import       = QPushButton(tr("btn_import_plan"))
        self.btn_calibrate    = QPushButton(tr("btn_calibrate"))
        self.btn_measure      = QPushButton(tr("btn_measure"))
        self.btn_place_ap     = QPushButton(tr("btn_place_ap"))
        self.btn_align        = QPushButton(tr("btn_align"))

        self.btn_new_floor.setEnabled(False)
        self.btn_import.setEnabled(False)
        self.btn_calibrate.setEnabled(False)
        self.btn_measure.setEnabled(False)
        self.btn_place_ap.setEnabled(False)
        self.btn_align.setEnabled(False)

        for btn in (self.btn_new_building, self.btn_new_floor, self.btn_import,
                    self.btn_calibrate, self.btn_measure, self.btn_place_ap,
                    self.btn_align):
            layout.addWidget(btn)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(sep)

        self.btn_delete_floor    = QPushButton(tr("btn_delete_floor"))
        self.btn_delete_building = QPushButton(tr("btn_delete_building"))
        self.btn_delete_floor.setEnabled(False)
        self.btn_delete_building.setEnabled(False)
        self.btn_delete_floor.setStyleSheet("color: #c0392b;")
        self.btn_delete_building.setStyleSheet("color: #c0392b;")
        layout.addWidget(self.btn_delete_floor)
        layout.addWidget(self.btn_delete_building)

        self.btn_new_building.clicked.connect(self._on_new_building)
        self.btn_new_floor.clicked.connect(self._on_new_floor)
        self.btn_import.clicked.connect(self._on_import)
        self.btn_calibrate.clicked.connect(self._on_calibrate)
        self.btn_measure.clicked.connect(self._on_measure)
        self.btn_place_ap.clicked.connect(self._on_place_ap)
        self.btn_align.clicked.connect(self._on_align)
        self.btn_delete_floor.clicked.connect(self._on_delete_floor)
        self.btn_delete_building.clicked.connect(self._on_delete_building)

    def refresh(self, reselect_floor_id: int | None = None):
        self.tree.clear()
        with get_session() as session:
            buildings = session.exec(select(Building).order_by(Building.name)).all()
            for building in buildings:
                b_item = QTreeWidgetItem([building.name])
                b_item.setData(0, _ROLE, ("building", building.id))
                floors = session.exec(
                    select(Floor)
                    .where(Floor.building_id == building.id)
                    .order_by(Floor.index)
                ).all()
                for floor in floors:
                    has_plan = session.exec(
                        select(FloorPlan).where(FloorPlan.floor_id == floor.id)
                    ).first() is not None
                    prefix = "📐" if has_plan else "  "
                    f_item = QTreeWidgetItem([f"{prefix} {floor.label}"])
                    f_item.setData(0, _ROLE, ("floor", floor.id))
                    b_item.addChild(f_item)
                    if reselect_floor_id == floor.id:
                        self.tree.setCurrentItem(f_item)
                        self._update_floor_buttons(floor.id, has_plan)
                self.tree.addTopLevelItem(b_item)
                b_item.setExpanded(True)

    def _on_item_clicked(self, item: QTreeWidgetItem, _col: int):
        data = item.data(0, _ROLE)
        if data is None:
            return
        kind, entity_id = data
        if kind == "building":
            self._current_building_id = entity_id
            self._current_floor_id = None
            self.btn_new_floor.setEnabled(True)
            self.btn_import.setEnabled(False)
            self.btn_calibrate.setEnabled(False)
            self.btn_align.setEnabled(False)
            self.btn_delete_building.setEnabled(True)
            self.btn_delete_floor.setEnabled(False)
            self.building_selected.emit(entity_id)
        elif kind == "floor":
            self._current_floor_id = entity_id
            self._current_building_id = None
            self.btn_new_floor.setEnabled(False)
            has_plan = self._floor_has_plan(entity_id)
            self._update_floor_buttons(entity_id, has_plan)
            self.btn_delete_floor.setEnabled(True)
            self.btn_delete_building.setEnabled(False)
            self.floor_selected.emit(entity_id)

    def _update_floor_buttons(self, floor_id: int, has_plan: bool):
        self._current_floor_id = floor_id
        self.btn_import.setEnabled(True)
        self.btn_calibrate.setEnabled(has_plan)
        self.btn_measure.setEnabled(has_plan)
        self.btn_place_ap.setEnabled(has_plan)
        self.btn_align.setEnabled(has_plan and self._has_floor_below(floor_id))

    def _floor_has_plan(self, floor_id: int) -> bool:
        with get_session() as session:
            return session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == floor_id)
            ).first() is not None

    def _has_floor_below(self, floor_id: int) -> bool:
        with get_session() as session:
            floor = session.get(Floor, floor_id)
            if not floor:
                return False
            return session.exec(
                select(Floor)
                .where(Floor.building_id == floor.building_id)
                .where(Floor.index < floor.index)
            ).first() is not None

    def _on_new_building(self):
        dialog = BuildingDialog(self)
        if dialog.exec():
            name, address = dialog.get_data()
            with get_session() as session:
                session.add(Building(name=name, address=address))
                session.commit()
            self.refresh()
            self.data_changed.emit()

    def _on_new_floor(self):
        if self._current_building_id is None:
            return
        dialog = FloorDialog(self)
        if dialog.exec():
            index, label, height, attenuation = dialog.get_data()
            with get_session() as session:
                session.add(Floor(
                    building_id=self._current_building_id,
                    index=index,
                    label=label,
                    height_m=height,
                    floor_attenuation_db=attenuation,
                ))
                session.commit()
            self.refresh()
            self.data_changed.emit()

    def _on_import(self):
        if self._current_floor_id is not None:
            self.import_plan_requested.emit(self._current_floor_id)

    def _on_calibrate(self):
        if self._current_floor_id is not None:
            self.calibrate_requested.emit(self._current_floor_id)

    def _on_measure(self):
        if self._current_floor_id is not None:
            self.measure_requested.emit(self._current_floor_id)

    def _on_align(self):
        if self._current_floor_id is not None:
            self.alignment_requested.emit(self._current_floor_id)

    def _on_place_ap(self):
        if self._current_floor_id is not None:
            self.place_ap_requested.emit(self._current_floor_id)

    def _on_delete_floor(self):
        floor_id = self._current_floor_id
        if floor_id is None:
            return
        with get_session() as session:
            floor = session.get(Floor, floor_id)
            if not floor:
                return
            label = floor.label
        reply = QMessageBox.question(
            self, tr("dlg_delete_floor_title"),
            tr("dlg_delete_floor_msg", label=label),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        with get_session() as session:
            self._delete_floor_data(session, floor_id)
            session.commit()
        self._current_floor_id = None
        self.btn_delete_floor.setEnabled(False)
        self.btn_import.setEnabled(False)
        self.btn_calibrate.setEnabled(False)
        self.btn_measure.setEnabled(False)
        self.btn_place_ap.setEnabled(False)
        self.btn_align.setEnabled(False)
        self.refresh()
        self.floor_deleted.emit()

    def _on_delete_building(self):
        building_id = self._current_building_id
        if building_id is None:
            return
        with get_session() as session:
            building = session.get(Building, building_id)
            if not building:
                return
            name = building.name
        reply = QMessageBox.question(
            self, tr("dlg_delete_building_title"),
            tr("dlg_delete_building_msg", name=name),
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        with get_session() as session:
            floors = session.exec(
                select(Floor).where(Floor.building_id == building_id)
            ).all()
            for floor in floors:
                self._delete_floor_data(session, floor.id)
            building = session.get(Building, building_id)
            session.delete(building)
            session.commit()
        self._current_building_id = None
        self.btn_new_floor.setEnabled(False)
        self.btn_delete_building.setEnabled(False)
        self.refresh()
        self.building_deleted.emit()

    @staticmethod
    def _delete_floor_data(session, floor_id: int):
        points = session.exec(
            select(MeasurementPoint).where(MeasurementPoint.floor_id == floor_id)
        ).all()
        for point in points:
            for scan in session.exec(
                select(MeasurementScan)
                .where(MeasurementScan.measurement_point_id == point.id)
            ).all():
                session.delete(scan)
            session.delete(point)
        for ap in session.exec(
            select(AccessPoint).where(AccessPoint.floor_id == floor_id)
        ).all():
            session.delete(ap)
        fp = session.exec(
            select(FloorPlan).where(FloorPlan.floor_id == floor_id)
        ).first()
        if fp:
            session.delete(fp)
        floor = session.get(Floor, floor_id)
        if floor:
            session.delete(floor)
