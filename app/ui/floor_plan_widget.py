import numpy as np
from PySide6.QtCore import Qt, QPointF, QTimer, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen, QPixmap, QPolygonF
from PySide6.QtWidgets import (
    QGraphicsPixmapItem, QGraphicsScene, QGraphicsView,
)

from ..services.interpolation import grid_to_rgba


def _signal_color(dbm: int) -> QColor:
    if dbm >= -65:
        return QColor("#2ecc71")
    if dbm >= -80:
        return QColor("#f39c12")
    return QColor("#e74c3c")


class FloorPlanWidget(QGraphicsView):
    calibration_ready = Signal(QPointF, QPointF)
    position_selected = Signal(QPointF)
    section_line_changed = Signal(QPointF, QPointF)
    ap_placed = Signal(QPointF)
    ap_moved = Signal(int, QPointF)   # ap_id, new_position

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self._plan_item = None
        self._heatmap_item: QGraphicsPixmapItem | None = None
        self._sim_heatmap_item: QGraphicsPixmapItem | None = None
        self._cal_mode = False
        self._measure_mode = False
        self._section_mode = False
        self._place_ap_mode = False
        self._cal_points: list[QPointF] = []
        self._cal_items = []
        self._section_points: list[QPointF] = []
        self._section_items = []
        self._ap_items: dict[int, list] = {}   # ap_id → graphics items
        self._measure_items: list = []
        self._move_ap_mode = False
        self._moving_ap_id: int | None = None
        self._highlighted_ap_id: int | None = None
        self._blink_visible = True
        self._blink_timer = QTimer(self)
        self._blink_timer.setInterval(450)
        self._blink_timer.timeout.connect(self._on_blink)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self._show_placeholder("Sélectionnez un étage")

    def _show_placeholder(self, text: str):
        self._scene.clear()
        self._plan_item = None
        self._heatmap_item = None
        self._sim_heatmap_item = None
        self._ap_items = {}
        self._measure_items = []
        self._scene.addText(text).setDefaultTextColor(QColor("#888888"))

    def load_floorplan(self, path: str):
        self._exit_calibration()
        self._exit_measure_mode()
        self._exit_section_mode()
        self._exit_place_ap_mode()
        self._scene.clear()
        self._plan_item = None
        self._heatmap_item = None
        self._sim_heatmap_item = None
        self._cal_items = []
        self._section_items = []
        self._ap_items = {}
        self._measure_items = []
        self.stop_highlight_ap()

        pixmap = QPixmap(path)
        if pixmap.isNull():
            self._show_placeholder("Impossible de charger l'image")
            return

        self._plan_item = self._scene.addPixmap(pixmap)
        self._scene.setSceneRect(pixmap.rect().toRectF())
        self.fitInView(self._scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    # ── Heatmap overlay ───────────────────────────────────────────────────

    def set_heatmap(self, grid: np.ndarray, plan_w: float, plan_h: float,
                    opacity: float = 0.7):
        """Render IDW grid as a semi-transparent overlay on the floor plan."""
        self.clear_heatmap()
        if self._plan_item is None:
            return

        H, W = grid.shape
        rgba = grid_to_rgba(grid)
        img = QImage(rgba.tobytes(), W, H, 4 * W, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(img).scaled(
            int(plan_w), int(plan_h),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._heatmap_item = self._scene.addPixmap(pixmap)
        self._heatmap_item.setZValue(5)
        self._heatmap_item.setOpacity(opacity)

    def clear_heatmap(self):
        if self._heatmap_item is not None:
            self._scene.removeItem(self._heatmap_item)
            self._heatmap_item = None

    def set_heatmap_opacity(self, opacity: float):
        if self._heatmap_item is not None:
            self._heatmap_item.setOpacity(opacity)

    # ── Simulated heatmap overlay ─────────────────────────────────────────

    def set_sim_heatmap(self, grid: np.ndarray, plan_w: float, plan_h: float,
                        opacity: float = 0.7):
        """Render simulated LDPL grid as an overlay below the measured heatmap."""
        self.clear_sim_heatmap()
        if self._plan_item is None:
            return

        H, W = grid.shape
        rgba = grid_to_rgba(grid)
        img = QImage(rgba.tobytes(), W, H, 4 * W, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(img).scaled(
            int(plan_w), int(plan_h),
            Qt.AspectRatioMode.IgnoreAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self._sim_heatmap_item = self._scene.addPixmap(pixmap)
        self._sim_heatmap_item.setZValue(4)   # below measured heatmap (z=5)
        self._sim_heatmap_item.setOpacity(opacity)

    def clear_sim_heatmap(self):
        if self._sim_heatmap_item is not None:
            self._scene.removeItem(self._sim_heatmap_item)
            self._sim_heatmap_item = None

    def set_sim_heatmap_opacity(self, opacity: float):
        if self._sim_heatmap_item is not None:
            self._sim_heatmap_item.setOpacity(opacity)

    # ── Measurement markers ───────────────────────────────────────────────

    def load_measurements(self, points: list[tuple[float, float, int]]):
        for x, y, sig in points:
            self._add_marker(x, y, sig)

    def add_measurement_marker(self, x_px: float, y_px: float, signal_dbm: int):
        r = 8
        color = _signal_color(signal_dbm)
        item = self._scene.addEllipse(
            x_px - r, y_px - r, r * 2, r * 2,
            QPen(color.darker(140), 1.5),
            QBrush(color),
        )
        item.setZValue(10)
        item.setToolTip(f"{signal_dbm} dBm")
        self._measure_items.append(item)

    def clear_measurement_markers(self):
        for item in self._measure_items:
            self._scene.removeItem(item)
        self._measure_items = []

    def center_on(self, x: float, y: float):
        self.centerOn(x, y)

    # ── AP markers ────────────────────────────────────────────────────────

    def load_access_points(self, aps: list[tuple[int, float, float, str]]):
        for ap_id, x, y, label in aps:
            self._add_ap_marker(ap_id, x, y, label)

    def add_ap_marker(self, ap_id: int, x_px: float, y_px: float, label: str):
        self._add_ap_marker(ap_id, x_px, y_px, label)

    def _add_ap_marker(self, ap_id: int, x: float, y: float, label: str):
        items = []
        r = 20

        halo = self._scene.addEllipse(
            x - r - 4, y - r - 4, (r + 4) * 2, (r + 4) * 2,
            QPen(Qt.PenStyle.NoPen),
            QBrush(QColor(255, 255, 255, 180)),
        )
        halo.setZValue(11)
        items.append(halo)

        diamond = QPolygonF([
            QPointF(x,     y - r),
            QPointF(x + r, y),
            QPointF(x,     y + r),
            QPointF(x - r, y),
        ])
        color = QColor("#8e44ad")
        body = self._scene.addPolygon(diamond, QPen(QColor("#ffffff"), 3.0), QBrush(color))
        body.setZValue(12)
        body.setToolTip(label)
        items.append(body)

        dot = self._scene.addEllipse(x - 4, y - 4, 8, 8,
                                     QPen(Qt.PenStyle.NoPen), QBrush(QColor("#ffffff")))
        dot.setZValue(13)
        items.append(dot)

        text = self._scene.addText(label)
        text.setDefaultTextColor(QColor("#ffffff"))
        font = text.font()
        font.setPointSize(9)
        font.setBold(True)
        text.setFont(font)
        br = text.boundingRect()
        bg = self._scene.addRect(
            x + r + 4, y - br.height() / 2, br.width() + 4, br.height(),
            QPen(Qt.PenStyle.NoPen), QBrush(QColor(0, 0, 0, 160)),
        )
        bg.setZValue(13)
        items.append(bg)
        text.setPos(x + r + 6, y - br.height() / 2)
        text.setZValue(14)
        items.append(text)

        self._ap_items[ap_id] = items

    def clear_ap_markers(self):
        self.stop_highlight_ap()
        for items in self._ap_items.values():
            for item in items:
                self._scene.removeItem(item)
        self._ap_items = {}

    # ── AP highlight (blink) ──────────────────────────────────────────────

    def highlight_ap(self, ap_id: int):
        self.stop_highlight_ap()
        if ap_id not in self._ap_items:
            return
        self._highlighted_ap_id = ap_id
        self._blink_visible = True
        self._blink_timer.start()

    def stop_highlight_ap(self):
        self._blink_timer.stop()
        if self._highlighted_ap_id is not None:
            for item in self._ap_items.get(self._highlighted_ap_id, []):
                item.setOpacity(1.0)
        self._highlighted_ap_id = None

    def _on_blink(self):
        if self._highlighted_ap_id not in self._ap_items:
            self.stop_highlight_ap()
            return
        self._blink_visible = not self._blink_visible
        opacity = 1.0 if self._blink_visible else 0.15
        for item in self._ap_items[self._highlighted_ap_id]:
            item.setOpacity(opacity)

    # ── Move AP mode ──────────────────────────────────────────────────────

    def start_move_ap_mode(self, ap_id: int):
        if self._plan_item is None:
            return
        self._move_ap_mode = True
        self._moving_ap_id = ap_id
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _exit_move_ap_mode(self):
        self._move_ap_mode = False
        self._moving_ap_id = None
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    def clear(self):
        self._exit_calibration()
        self._exit_measure_mode()
        self._exit_section_mode()
        self._exit_place_ap_mode()
        self._exit_move_ap_mode()
        self.stop_highlight_ap()
        self._section_items = []
        self._show_placeholder("Sélectionnez un étage")

    # ── Calibration mode ──────────────────────────────────────────────────

    def start_calibration(self):
        if self._plan_item is None:
            return
        for item in self._cal_items:
            self._scene.removeItem(item)
        self._cal_items = []
        self._cal_points = []
        self._cal_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _exit_calibration(self):
        self._cal_mode = False
        self._cal_points = []
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # ── Section line mode ─────────────────────────────────────────────────

    def start_section_mode(self):
        if self._plan_item is None:
            return
        for item in self._section_items:
            self._scene.removeItem(item)
        self._section_items = []
        self._section_points = []
        self._section_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _exit_section_mode(self):
        self._section_mode = False
        self._section_points = []
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # ── Measure mode ──────────────────────────────────────────────────────

    def start_measure_mode(self):
        if self._plan_item is None:
            return
        self._measure_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _exit_measure_mode(self):
        self._measure_mode = False
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # ── Place AP mode ─────────────────────────────────────────────────────

    def start_place_ap_mode(self):
        if self._plan_item is None:
            return
        self._place_ap_mode = True
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def _exit_place_ap_mode(self):
        self._place_ap_mode = False
        self.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        self.unsetCursor()

    # ── Events ────────────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            super().mousePressEvent(event)
            return

        pos = self.mapToScene(event.position().toPoint())

        if self._cal_mode:
            self._cal_points.append(pos)
            dot = self._scene.addEllipse(
                pos.x() - 5, pos.y() - 5, 10, 10,
                QPen(QColor("#e74c3c"), 2),
                QBrush(QColor("#e74c3c")),
            )
            self._cal_items.append(dot)
            if len(self._cal_points) == 2:
                p1, p2 = self._cal_points
                self._cal_items.append(self._scene.addLine(
                    p1.x(), p1.y(), p2.x(), p2.y(),
                    QPen(QColor("#e74c3c"), 2),
                ))
                self._exit_calibration()
                self.calibration_ready.emit(p1, p2)

        elif self._section_mode:
            self._section_points.append(pos)
            dot = self._scene.addEllipse(
                pos.x() - 5, pos.y() - 5, 10, 10,
                QPen(QColor("#e67e22"), 2),
                QBrush(QColor("#f39c12")),
            )
            dot.setZValue(9)
            self._section_items.append(dot)
            if len(self._section_points) == 2:
                p1, p2 = self._section_points
                line = self._scene.addLine(
                    p1.x(), p1.y(), p2.x(), p2.y(),
                    QPen(QColor("#f1c40f"), 2, Qt.PenStyle.DashLine),
                )
                line.setZValue(8)
                self._section_items.append(line)
                self._exit_section_mode()
                self.section_line_changed.emit(p1, p2)

        elif self._measure_mode:
            self._exit_measure_mode()
            self.position_selected.emit(pos)

        elif self._place_ap_mode:
            self._exit_place_ap_mode()
            self.ap_placed.emit(pos)

        elif self._move_ap_mode:
            ap_id = self._moving_ap_id
            self._exit_move_ap_mode()
            self.stop_highlight_ap()
            self.ap_moved.emit(ap_id, pos)

        else:
            super().mousePressEvent(event)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)
