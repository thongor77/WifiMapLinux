import shutil
from math import sqrt

from PySide6.QtCore import Qt, QPointF, QThread, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFileDialog, QInputDialog, QMainWindow, QMessageBox,
    QSplitter, QStatusBar, QVBoxLayout, QWidget,
)
from .section_view import SectionView
from sqlmodel import select

from ..models.building import Building
from ..models.database import DATA_DIR, get_session
from ..models.floor import Floor, FloorPlan
from ..models.measurement import MeasurementPoint, MeasurementScan
from .ap_panel import APPanel
from .building_panel import BuildingPanel
from .floor_plan_widget import FloorPlanWidget
from .floor_tab_bar import FloorTabBar
from .heatmap_controls import HeatmapControls


class _ScanThread(QThread):
    result = Signal(list)

    def run(self):
        from ..services.scanner import scan_wifi
        self.result.emit(scan_wifi())


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WifiMapLinux")
        self.resize(1280, 800)
        self._current_floor_id: int | None = None
        self._pending_pos: QPointF | None = None
        self._scan_thread: _ScanThread | None = None
        self._section_p1: QPointF | None = None
        self._section_p2: QPointF | None = None
        self._section_floor_id: int | None = None
        self._current_measured_grid = None   # np.ndarray | None
        self._current_sim_grid = None        # np.ndarray | None
        self._setup_ui()
        self._setup_menu()

    def _setup_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.building_panel = BuildingPanel()
        self.building_panel.setFixedWidth(270)
        splitter.addWidget(self.building_panel)

        # Right panel: tab bar + floor plan + section view + heatmap controls
        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.floor_tab_bar = FloorTabBar()
        right_layout.addWidget(self.floor_tab_bar)

        self.floor_plan_widget = FloorPlanWidget()
        self.section_view = SectionView()

        plan_section_splitter = QSplitter(Qt.Orientation.Vertical)
        plan_section_splitter.addWidget(self.floor_plan_widget)
        plan_section_splitter.addWidget(self.section_view)
        plan_section_splitter.setSizes([540, 160])
        right_layout.addWidget(plan_section_splitter, stretch=1)

        self.heatmap_controls = HeatmapControls()
        right_layout.addWidget(self.heatmap_controls)

        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        self.ap_panel = APPanel()
        self.ap_panel.setFixedWidth(240)
        splitter.addWidget(self.ap_panel)

        self.setCentralWidget(splitter)
        self.setStatusBar(QStatusBar())

        # Connections
        self.building_panel.building_selected.connect(self._on_building_selected)
        self.building_panel.floor_selected.connect(self._on_floor_selected)
        self.building_panel.import_plan_requested.connect(self._on_import_plan)
        self.building_panel.calibrate_requested.connect(self._on_calibrate)
        self.building_panel.measure_requested.connect(self._on_measure_requested)
        self.building_panel.alignment_requested.connect(self._on_alignment_requested)
        self.building_panel.place_ap_requested.connect(self._on_place_ap_requested)
        self.building_panel.building_deleted.connect(self._on_entity_deleted)
        self.building_panel.floor_deleted.connect(self._on_entity_deleted)
        self.ap_panel.ap_deleted.connect(self._on_ap_panel_changed)
        self.ap_panel.ap_edited.connect(self._on_ap_panel_changed)
        self.ap_panel.ap_highlight_requested.connect(self.floor_plan_widget.highlight_ap)
        self.ap_panel.ap_unhighlight_requested.connect(self.floor_plan_widget.stop_highlight_ap)
        self.ap_panel.ap_move_requested.connect(self._on_ap_move_requested)
        self.floor_plan_widget.ap_moved.connect(self._on_ap_moved)
        self.floor_tab_bar.floor_selected.connect(self._on_floor_selected)
        self.floor_plan_widget.calibration_ready.connect(self._on_calibration_points)
        self.floor_plan_widget.position_selected.connect(self._on_position_selected)
        self.floor_plan_widget.ap_placed.connect(self._on_ap_placed)
        self.heatmap_controls.toggled.connect(self._on_heatmap_toggled)
        self.heatmap_controls.sim_toggled.connect(self._on_sim_toggled)
        self.heatmap_controls.ssid_changed.connect(self._on_heatmap_ssid_changed)
        self.heatmap_controls.opacity_changed.connect(self._on_heatmap_opacity)
        self.heatmap_controls.section_requested.connect(self._on_section_requested)
        self.floor_plan_widget.section_line_changed.connect(self._on_section_line_changed)

    def _setup_menu(self):
        file_menu = self.menuBar().addMenu("Fichier")
        quit_action = QAction("Quitter", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        export_menu = self.menuBar().addMenu("Export")
        png_action = QAction("Exporter étage actuel (PNG)…", self)
        png_action.setShortcut("Ctrl+E")
        png_action.triggered.connect(self._on_export_png)
        export_menu.addAction(png_action)

        pdf_action = QAction("Rapport de couverture (PDF)…", self)
        pdf_action.setShortcut("Ctrl+Shift+E")
        pdf_action.triggered.connect(self._on_export_pdf)
        export_menu.addAction(pdf_action)

    # ── Delete ────────────────────────────────────────────────────────────

    def _on_entity_deleted(self):
        self._current_floor_id = None
        self._current_measured_grid = None
        self._current_sim_grid = None
        self._section_p1 = None
        self._section_p2 = None
        self._section_floor_id = None
        self.floor_tab_bar.populate([])
        self.floor_plan_widget.clear()
        self.section_view.update_section([], 0)
        self.ap_panel.clear()
        self.statusBar().showMessage("")

    # ── Building / floor selection ────────────────────────────────────────

    def _on_building_selected(self, building_id: int):
        with get_session() as session:
            floors = session.exec(
                select(Floor)
                .where(Floor.building_id == building_id)
                .order_by(Floor.index)
            ).all()
            tab_data = [(f.id, f.label) for f in floors]
            first_id = floors[0].id if floors else None

        self.floor_tab_bar.populate(tab_data)
        if first_id is not None:
            self.floor_tab_bar.set_active(first_id)
            self._on_floor_selected(first_id)

    def _populate_floor_tabs(self, floor_id: int):
        with get_session() as session:
            floor = session.get(Floor, floor_id)
            if not floor:
                return
            floors = session.exec(
                select(Floor)
                .where(Floor.building_id == floor.building_id)
                .order_by(Floor.index)
            ).all()
            tab_data = [(f.id, f.label) for f in floors]
        self.floor_tab_bar.populate(tab_data)
        self.floor_tab_bar.set_active(floor_id)

    def _on_alignment_requested(self, floor_id: int):
        from .dialogs.alignment_dialog import AlignmentDialog
        with get_session() as session:
            cur_fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == floor_id)
            ).first()
            cur_floor = session.get(Floor, floor_id)
            if not cur_fp or not cur_floor:
                return
            ref_floor = session.exec(
                select(Floor)
                .where(Floor.building_id == cur_floor.building_id)
                .where(Floor.index < cur_floor.index)
                .order_by(Floor.index.desc())
            ).first()
            if not ref_floor:
                QMessageBox.warning(self, "Recalage", "Aucun étage inférieur trouvé.")
                return
            ref_fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == ref_floor.id)
            ).first()
            if not ref_fp:
                QMessageBox.warning(
                    self, "Recalage",
                    f"L'étage « {ref_floor.label} » n'a pas de plan importé.",
                )
                return
            if not ref_fp.scale_px_per_m:
                QMessageBox.warning(
                    self, "Recalage",
                    f"L'étage « {ref_floor.label} » n'est pas encore calibré.",
                )
                return
            ref_path = ref_fp.image_path
            cur_path = cur_fp.image_path
            ref_scale = ref_fp.scale_px_per_m
            cur_scale = cur_fp.scale_px_per_m
            saved_offset = (cur_floor.offset_x_m, cur_floor.offset_y_m)

        dialog = AlignmentDialog(ref_path, cur_path, ref_scale, cur_scale,
                                 initial_offset_m=saved_offset, parent=self)
        if dialog.exec():
            ox_m, oy_m = dialog.offset_m()
            with get_session() as session:
                floor = session.get(Floor, floor_id)
                if floor:
                    floor.offset_x_m = ox_m
                    floor.offset_y_m = oy_m
                    session.add(floor)
                    session.commit()
            self.statusBar().showMessage(
                f"Recalage sauvegardé — Δx={ox_m:.2f} m, Δy={oy_m:.2f} m"
            )

    def _on_floor_selected(self, floor_id: int):
        self._populate_floor_tabs(floor_id)
        self._current_floor_id = floor_id
        self._current_measured_grid = None
        self._current_sim_grid = None
        with get_session() as session:
            floor = session.get(Floor, floor_id)
            self.ap_panel.load_floor(floor_id, floor.label if floor else "")
            fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == floor_id)
            ).first()
            if fp:
                self.floor_plan_widget.load_floorplan(fp.image_path)
                self._load_measurement_markers(floor_id, session)
                self._load_ap_markers(floor_id, session)
                self._populate_ssids(floor_id, session)
                if self.heatmap_controls.is_active():
                    self._compute_heatmap(fp)
                if fp.scale_px_per_m:
                    self.statusBar().showMessage(
                        f"Échelle : {fp.scale_px_per_m:.1f} px/m — {fp.cal_dist_m} m"
                    )
                else:
                    self.statusBar().showMessage("Plan importé — calibration requise")
            else:
                self.floor_plan_widget.clear()
                self.statusBar().showMessage(
                    "Aucun plan pour cet étage — cliquez 'Importer plan PNG'"
                )
        if self.heatmap_controls.sim_is_active():
            self._refresh_sim_heatmap()

    def _load_ap_markers(self, floor_id: int, session):
        from ..models.access_point import AccessPoint
        aps = session.exec(
            select(AccessPoint).where(AccessPoint.floor_id == floor_id)
        ).all()
        for ap in aps:
            self.floor_plan_widget.add_ap_marker(ap.id, ap.x_px, ap.y_px, ap.label)

    def _load_measurement_markers(self, floor_id: int, session):
        points = session.exec(
            select(MeasurementPoint).where(MeasurementPoint.floor_id == floor_id)
        ).all()
        markers = []
        for pt in points:
            scans = session.exec(
                select(MeasurementScan)
                .where(MeasurementScan.measurement_point_id == pt.id)
            ).all()
            best = max((s.signal_dbm for s in scans), default=-100)
            markers.append((pt.x_px, pt.y_px, best))
        self.floor_plan_widget.load_measurements(markers)

    def _populate_ssids(self, floor_id: int, session):
        pts = session.exec(
            select(MeasurementPoint).where(MeasurementPoint.floor_id == floor_id)
        ).all()
        ssids: list[str] = []
        for pt in pts:
            scans = session.exec(
                select(MeasurementScan)
                .where(MeasurementScan.measurement_point_id == pt.id)
            ).all()
            ssids.extend(s.ssid for s in scans if s.ssid)
        self.heatmap_controls.populate_ssids(list(set(ssids)))

    # ── Import plan ───────────────────────────────────────────────────────

    def _on_import_plan(self, floor_id: int):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer un plan", "", "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return
        dest_dir = DATA_DIR / str(floor_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / "floorplan.png"
        shutil.copy(path, dest)

        from PySide6.QtGui import QPixmap
        pixmap = QPixmap(str(dest))
        w, h = pixmap.width(), pixmap.height()

        with get_session() as session:
            existing = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == floor_id)
            ).first()
            if existing:
                existing.image_path = str(dest)
                existing.width_px, existing.height_px = w, h
                existing.scale_px_per_m = None
                session.add(existing)
            else:
                session.add(FloorPlan(
                    floor_id=floor_id, image_path=str(dest),
                    width_px=w, height_px=h,
                ))
            session.commit()

        self.building_panel.refresh(reselect_floor_id=floor_id)
        self._on_floor_selected(floor_id)
        self.statusBar().showMessage(
            f"Plan importé ({w}×{h} px) — cliquez 'Calibrer l'échelle'"
        )

    # ── Calibration ───────────────────────────────────────────────────────

    def _on_calibrate(self, _floor_id: int):
        self.floor_plan_widget.start_calibration()
        self.statusBar().showMessage("Calibration : cliquez 2 points sur le plan")

    def _on_calibration_points(self, p1: QPointF, p2: QPointF):
        pixel_dist = sqrt((p2.x() - p1.x()) ** 2 + (p2.y() - p1.y()) ** 2)
        dist_m, ok = QInputDialog.getDouble(
            self, "Calibration — distance réelle",
            f"Distance entre les 2 points ({pixel_dist:.1f} px) en mètres :",
            1.0, 0.01, 999.0, 2,
        )
        if not ok or self._current_floor_id is None:
            return
        scale = pixel_dist / dist_m
        with get_session() as session:
            fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == self._current_floor_id)
            ).first()
            if fp:
                fp.scale_px_per_m = scale
                fp.cal_p1_x, fp.cal_p1_y = int(p1.x()), int(p1.y())
                fp.cal_p2_x, fp.cal_p2_y = int(p2.x()), int(p2.y())
                fp.cal_dist_m = dist_m
                session.add(fp)
                session.commit()
        self.statusBar().showMessage(
            f"Échelle calibrée : {scale:.1f} px/m  ({dist_m:.2f} m)"
        )

    # ── Measure flow ──────────────────────────────────────────────────────

    def _on_measure_requested(self, _floor_id: int):
        self.floor_plan_widget.start_measure_mode()
        self.statusBar().showMessage("📡  Cliquez sur votre position actuelle sur le plan")

    def _on_position_selected(self, pos: QPointF):
        self._pending_pos = pos
        self.statusBar().showMessage("Scan Wi-Fi en cours…")
        self.building_panel.setEnabled(False)
        self._scan_thread = _ScanThread(self)
        self._scan_thread.result.connect(self._on_scan_result)
        self._scan_thread.start()

    def _on_scan_result(self, networks: list):
        self.building_panel.setEnabled(True)
        if self._pending_pos is None or self._current_floor_id is None:
            return

        if not networks:
            QMessageBox.warning(
                self, "Aucun réseau détecté",
                "Le scan n'a retourné aucun réseau.\n"
                "Vérifiez que le Wi-Fi est activé et qu'iw/nmcli est disponible.",
            )
            self.statusBar().showMessage("Scan : aucun réseau détecté")
            return

        from .dialogs.scan_dialog import ScanDialog
        dialog = ScanDialog(networks, self)
        if not dialog.exec():
            self.statusBar().showMessage("Mesure annulée")
            return

        label = dialog.get_label()
        pos = self._pending_pos
        floor_id = self._current_floor_id
        best_signal = max(n.signal_dbm for n in networks)

        with get_session() as session:
            pt = MeasurementPoint(
                floor_id=floor_id, x_px=pos.x(), y_px=pos.y(), label=label,
            )
            session.add(pt)
            session.flush()
            for net in networks:
                session.add(MeasurementScan(
                    measurement_point_id=pt.id,
                    ssid=net.ssid, bssid=net.bssid,
                    signal_dbm=net.signal_dbm,
                    channel=net.channel, frequency_mhz=net.frequency_mhz,
                ))
            session.commit()

        self.floor_plan_widget.add_measurement_marker(pos.x(), pos.y(), best_signal)

        with get_session() as session:
            self._populate_ssids(floor_id, session)
        if self.heatmap_controls.is_active():
            self._refresh_heatmap()
        self._refresh_section()

        n = len(networks)
        self.statusBar().showMessage(
            f"Mesure enregistrée — {n} réseau{'x' if n > 1 else ''} · "
            f"meilleur signal : {best_signal} dBm"
        )

    # ── Section (coupe verticale) ─────────────────────────────────────────

    def _on_section_requested(self):
        self.floor_plan_widget.start_section_mode()
        self.statusBar().showMessage(
            "Coupe : cliquez 2 points sur le plan pour définir la ligne de coupe"
        )

    def _on_section_line_changed(self, p1: QPointF, p2: QPointF):
        self._section_p1 = p1
        self._section_p2 = p2
        self._section_floor_id = self._current_floor_id
        self._refresh_section()

    def _refresh_section(self):
        if self._section_floor_id is None or self._section_p1 is None:
            return

        from math import sqrt as _sqrt
        from ..services.interpolation import idw_points

        with get_session() as session:
            ref_fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == self._section_floor_id)
            ).first()
            if not ref_fp or not ref_fp.scale_px_per_m:
                return
            ref_floor = session.get(Floor, self._section_floor_id)
            if not ref_floor:
                return

            floors = session.exec(
                select(Floor)
                .where(Floor.building_id == ref_floor.building_id)
                .order_by(Floor.index)
            ).all()

            # Accumulate absolute XY offsets (metres, relative to floor-0 origin)
            abs_off: dict[int, tuple[float, float]] = {}
            abs_off[floors[0].id] = (0.0, 0.0)
            for i in range(1, len(floors)):
                prev = floors[i - 1]
                cur  = floors[i]
                px, py = abs_off[prev.id]
                abs_off[cur.id] = (px + cur.offset_x_m, py + cur.offset_y_m)

            # Section line endpoints in building metres
            ref_ox, ref_oy = abs_off[self._section_floor_id]
            scale = ref_fp.scale_px_per_m
            bx1 = ref_ox + self._section_p1.x() / scale
            by1 = ref_oy + self._section_p1.y() / scale
            bx2 = ref_ox + self._section_p2.x() / scale
            by2 = ref_oy + self._section_p2.y() / scale
            line_len = _sqrt((bx2 - bx1) ** 2 + (by2 - by1) ** 2)
            if line_len < 0.01:
                return

            ssid_filter = self.heatmap_controls.selected_ssid()
            N = 200

            # Pre-compute t-parameter sample positions along the line
            t_vals = [i / (N - 1) for i in range(N)]

            bands = []
            for floor in floors:
                fps = session.exec(
                    select(FloorPlan).where(FloorPlan.floor_id == floor.id)
                ).first()
                if not fps or not fps.scale_px_per_m:
                    bands.append((floor.label, floor.height_m, None))
                    continue

                pts = session.exec(
                    select(MeasurementPoint)
                    .where(MeasurementPoint.floor_id == floor.id)
                ).all()

                source: list[tuple[float, float, float]] = []
                for pt in pts:
                    scans = session.exec(
                        select(MeasurementScan)
                        .where(MeasurementScan.measurement_point_id == pt.id)
                    ).all()
                    relevant = [
                        s.signal_dbm for s in scans
                        if (not ssid_filter or s.ssid == ssid_filter)
                    ]
                    if relevant:
                        source.append((pt.x_px, pt.y_px, max(relevant)))

                if not source:
                    bands.append((floor.label, floor.height_m, None))
                    continue

                # Convert building-coord sample points to this floor's pixel coords
                ox, oy = abs_off[floor.id]
                s = fps.scale_px_per_m
                queries = [
                    ((bx1 + t * (bx2 - bx1) - ox) * s,
                     (by1 + t * (by2 - by1) - oy) * s)
                    for t in t_vals
                ]
                rssi = idw_points(source, queries)
                bands.append((floor.label, floor.height_m, rssi))

        self.section_view.update_section(bands, line_len)
        self.statusBar().showMessage(
            f"Coupe mise à jour — {line_len:.1f} m · {len(floors)} étage(s)"
        )

    # ── Heatmap controls ──────────────────────────────────────────────────

    def _on_heatmap_toggled(self, checked: bool):
        if checked:
            self._refresh_heatmap()
        else:
            self.floor_plan_widget.clear_heatmap()

    def _on_heatmap_ssid_changed(self, _ssid: str):
        if self.heatmap_controls.is_active():
            self._refresh_heatmap()
        self._refresh_section()

    def _on_heatmap_opacity(self, value: int):
        opacity = value / 100.0
        self.floor_plan_widget.set_heatmap_opacity(opacity)
        self.floor_plan_widget.set_sim_heatmap_opacity(opacity)

    def _refresh_heatmap(self):
        if self._current_floor_id is None:
            return
        with get_session() as session:
            fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == self._current_floor_id)
            ).first()
            if fp:
                self._compute_heatmap(fp)

    # ── Virtual AP placement ──────────────────────────────────────────────

    def _on_place_ap_requested(self, _floor_id: int):
        self.floor_plan_widget.start_place_ap_mode()
        self.statusBar().showMessage("AP virtuel : cliquez sur la position du point d'accès")

    def _on_ap_placed(self, pos):
        if self._current_floor_id is None:
            return
        from .dialogs.ap_dialog import APDialog
        from ..models.access_point import AccessPoint
        dialog = APDialog(parent=self)
        if not dialog.exec():
            self.statusBar().showMessage("Placement AP annulé")
            return
        label, tx, freq = dialog.get_data()
        with get_session() as session:
            ap = AccessPoint(
                floor_id=self._current_floor_id,
                x_px=pos.x(), y_px=pos.y(),
                label=label, tx_power_dbm=tx, frequency_mhz=freq,
            )
            session.add(ap)
            session.commit()
            session.refresh(ap)
            ap_id = ap.id
        self.floor_plan_widget.add_ap_marker(ap_id, pos.x(), pos.y(), label)
        self.ap_panel.refresh()
        if self.heatmap_controls.sim_is_active():
            self._refresh_sim_heatmap()

    def _on_ap_move_requested(self, ap_id: int):
        self.floor_plan_widget.start_move_ap_mode(ap_id)
        self.statusBar().showMessage("Cliquez sur la nouvelle position de l'AP")

    def _on_ap_moved(self, ap_id: int, pos):
        from ..models.access_point import AccessPoint
        with get_session() as session:
            ap = session.get(AccessPoint, ap_id)
            if ap:
                ap.x_px = pos.x()
                ap.y_px = pos.y()
                session.add(ap)
                session.commit()
        self._on_ap_panel_changed(self._current_floor_id)
        self.statusBar().showMessage("AP repositionné")

    def _on_ap_panel_changed(self, floor_id: int):
        if floor_id != self._current_floor_id:
            return
        self.floor_plan_widget.clear_ap_markers()
        with get_session() as session:
            self._load_ap_markers(floor_id, session)
        if self.heatmap_controls.sim_is_active():
            self._refresh_sim_heatmap()

    # ── Simulation heatmap ────────────────────────────────────────────────

    def _on_sim_toggled(self, checked: bool):
        if checked:
            self._refresh_sim_heatmap()
        else:
            self.floor_plan_widget.clear_sim_heatmap()

    def _refresh_sim_heatmap(self):
        if self._current_floor_id is None:
            return
        from ..models.access_point import AccessPoint
        from ..services.propagation import APSimInfo, simulate_floor

        with get_session() as session:
            fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == self._current_floor_id)
            ).first()
            if not fp or not fp.scale_px_per_m:
                self.statusBar().showMessage("Simulation : plan non calibré pour cet étage")
                return

            target_floor = session.get(Floor, self._current_floor_id)
            if not target_floor:
                return

            floors = session.exec(
                select(Floor)
                .where(Floor.building_id == target_floor.building_id)
                .order_by(Floor.index)
            ).all()

            # Absolute XY offsets (same logic as section view)
            abs_off: dict[int, tuple[float, float]] = {}
            abs_off[floors[0].id] = (0.0, 0.0)
            for i in range(1, len(floors)):
                px, py = abs_off[floors[i - 1].id]
                abs_off[floors[i].id] = (px + floors[i].offset_x_m, py + floors[i].offset_y_m)

            # Z heights: cumulative sum of floor heights (AP sits at floor base)
            z_heights: dict[int, float] = {}
            z = 0.0
            for f in floors:
                z_heights[f.id] = z
                z += f.height_m

            floor_by_id = {f.id: f for f in floors}
            all_floor_ids = [f.id for f in floors]

            aps_db = session.exec(
                select(AccessPoint).where(AccessPoint.floor_id.in_(all_floor_ids))
            ).all()

            if not aps_db:
                self.floor_plan_widget.clear_sim_heatmap()
                self.statusBar().showMessage("Simulation : aucun AP virtuel placé (bouton 'Placer AP virtuel')")
                return

            # Fetch FloorPlan for each AP floor (needed for pixel→metre conversion)
            ap_fps: dict[int, FloorPlan | None] = {}
            for ap in aps_db:
                if ap.floor_id not in ap_fps:
                    ap_fps[ap.floor_id] = session.exec(
                        select(FloorPlan).where(FloorPlan.floor_id == ap.floor_id)
                    ).first()

            ap_infos: list[APSimInfo] = []
            for ap in aps_db:
                ap_fp = ap_fps.get(ap.floor_id)
                if not ap_fp or not ap_fp.scale_px_per_m:
                    continue
                ap_floor = floor_by_id[ap.floor_id]
                ox, oy = abs_off[ap.floor_id]
                ap_infos.append(APSimInfo(
                    bx_m=ox + ap.x_px / ap_fp.scale_px_per_m,
                    by_m=oy + ap.y_px / ap_fp.scale_px_per_m,
                    z_m=z_heights[ap.floor_id],
                    floor_index=ap_floor.index,
                    tx_dbm=ap.tx_power_dbm,
                    freq_mhz=ap.frequency_mhz,
                    faf_db=ap_floor.floor_attenuation_db,
                ))

            if not ap_infos:
                self.statusBar().showMessage("Simulation : aucun AP sur un étage calibré")
                return

            tox, toy = abs_off[target_floor.id]
            tz = z_heights[target_floor.id]
            width_px, height_px = fp.width_px, fp.height_px
            scale = fp.scale_px_per_m

        grid = simulate_floor(
            ap_infos,
            target_floor.index,
            tz, tox, toy, scale,
            width_px, height_px,
        )
        self._current_sim_grid = grid
        self.floor_plan_widget.set_sim_heatmap(
            grid, width_px, height_px,
            opacity=self.heatmap_controls.opacity(),
        )
        self.statusBar().showMessage(
            f"Simulation LDPL — {len(ap_infos)} AP(s) · {target_floor.label}"
        )

    # ── Export ────────────────────────────────────────────────────────────

    def _on_export_png(self):
        if self._current_floor_id is None:
            QMessageBox.warning(self, "Export PNG", "Aucun étage sélectionné.")
            return
        with get_session() as session:
            fp = session.exec(
                select(FloorPlan).where(FloorPlan.floor_id == self._current_floor_id)
            ).first()
            if not fp:
                QMessageBox.warning(self, "Export PNG", "Aucun plan importé pour cet étage.")
                return
            floor = session.get(Floor, self._current_floor_id)
            building = session.get(Building, floor.building_id) if floor else None
            meas_count = len(session.exec(
                select(MeasurementPoint).where(MeasurementPoint.floor_id == self._current_floor_id)
            ).all())
            plan_path = fp.image_path
            floor_name = floor.label if floor else "?"
            building_name = building.name if building else "?"

        # Choose grid: simulation if active, measured if active, else None
        grid = None
        if self.heatmap_controls.sim_is_active() and self._current_sim_grid is not None:
            grid = self._current_sim_grid
        elif self.heatmap_controls.is_active() and self._current_measured_grid is not None:
            grid = self._current_measured_grid

        output_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter PNG", f"{floor_name}.png", "Images PNG (*.png)"
        )
        if not output_path:
            return

        from ..services.export import export_floor_png
        try:
            export_floor_png(
                output_path=output_path,
                plan_path=plan_path,
                grid=grid,
                building_name=building_name,
                floor_name=floor_name,
                ssid_label=self.heatmap_controls.selected_ssid(),
                measurement_count=meas_count,
            )
            self.statusBar().showMessage(f"PNG exporté : {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur export PNG", str(e))

    def _on_export_pdf(self):
        if self._current_floor_id is None:
            QMessageBox.warning(self, "Export PDF", "Aucun étage sélectionné.")
            return

        from ..services.interpolation import idw
        from ..services.export import export_building_pdf

        with get_session() as session:
            floor = session.get(Floor, self._current_floor_id)
            if not floor:
                return
            building = session.get(Building, floor.building_id)
            building_name = building.name if building else "?"

            floors = session.exec(
                select(Floor)
                .where(Floor.building_id == floor.building_id)
                .order_by(Floor.index)
            ).all()

            ssid_filter = self.heatmap_controls.selected_ssid()
            floors_data: list[dict] = []

            for f in floors:
                fp = session.exec(
                    select(FloorPlan).where(FloorPlan.floor_id == f.id)
                ).first()
                pts = session.exec(
                    select(MeasurementPoint).where(MeasurementPoint.floor_id == f.id)
                ).all()
                meas_count = len(pts)

                grid = None
                if fp and fp.scale_px_per_m and len(pts) >= 2:
                    points: list[tuple[float, float, float]] = []
                    for pt in pts:
                        scans = session.exec(
                            select(MeasurementScan)
                            .where(MeasurementScan.measurement_point_id == pt.id)
                        ).all()
                        relevant = [
                            s.signal_dbm for s in scans
                            if not ssid_filter or s.ssid == ssid_filter
                        ]
                        if relevant:
                            points.append((pt.x_px, pt.y_px, max(relevant)))
                    if len(points) >= 2:
                        grid = idw(points, fp.width_px, fp.height_px)

                floors_data.append({
                    "name": f.label,
                    "plan_path": fp.image_path if fp else None,
                    "grid": grid,
                    "measurement_count": meas_count,
                })

        output_path, _ = QFileDialog.getSaveFileName(
            self, "Rapport de couverture", f"{building_name}.pdf", "PDF (*.pdf)"
        )
        if not output_path:
            return

        try:
            export_building_pdf(
                output_path=output_path,
                building_name=building_name,
                floors=floors_data,
                ssid_label=ssid_filter,
            )
            self.statusBar().showMessage(f"PDF exporté : {output_path}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur export PDF", str(e))

    def _compute_heatmap(self, fp: FloorPlan):
        from ..services.interpolation import idw
        ssid_filter = self.heatmap_controls.selected_ssid()

        with get_session() as session:
            pts = session.exec(
                select(MeasurementPoint)
                .where(MeasurementPoint.floor_id == fp.floor_id)
            ).all()

            points: list[tuple[float, float, float]] = []
            for pt in pts:
                scans = session.exec(
                    select(MeasurementScan)
                    .where(MeasurementScan.measurement_point_id == pt.id)
                ).all()
                if ssid_filter:
                    relevant = [s.signal_dbm for s in scans if s.ssid == ssid_filter]
                else:
                    relevant = [s.signal_dbm for s in scans]
                if relevant:
                    points.append((pt.x_px, pt.y_px, max(relevant)))

        if len(points) < 2:
            self.statusBar().showMessage(
                "Heatmap : au moins 2 points de mesure requis"
            )
            return

        grid = idw(points, fp.width_px, fp.height_px)
        self._current_measured_grid = grid
        self.floor_plan_widget.set_heatmap(
            grid, fp.width_px, fp.height_px,
            opacity=self.heatmap_controls.opacity(),
        )
        self.statusBar().showMessage(
            f"Heatmap générée — {len(points)} points"
            + (f" · {ssid_filter}" if ssid_filter else "")
        )
