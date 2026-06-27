from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QPixmap, QTransform
from PySide6.QtWidgets import (
    QDialog, QDoubleSpinBox, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


class _ResizableOverlay(QGraphicsPixmapItem):
    """
    Semi-transparent overlay supporting independent X/Y scaling.

    Three handles (blue squares):
    - Right-center  → drag to change width only  (cursor ↔)
    - Bottom-center → drag to change height only (cursor ↕)
    - Bottom-right  → drag to change both        (cursor ↘)
    Dragging anywhere else translates the item.
    """

    _H = 14        # handle visual size in screen pixels (compensated)
    _RIGHT  = "right"
    _BOTTOM = "bottom"
    _CORNER = "corner"

    def __init__(self, pixmap: QPixmap):
        super().__init__(pixmap)
        self._sx = 1.0
        self._sy = 1.0
        self.setOpacity(0.5)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(0, 0)
        self._active = None          # which handle is being dragged
        self._origin_scene = QPointF()
        self._start_mouse = QPointF()
        self._start_sx = 1.0
        self._start_sy = 1.0
        self.scale_x_changed_cb = None
        self.scale_y_changed_cb = None

    # ── Scale helpers ─────────────────────────────────────────────────────

    def set_scale_xy(self, sx: float, sy: float):
        self._sx = max(0.1, min(5.0, sx))
        self._sy = max(0.1, min(5.0, sy))
        self.setTransform(QTransform().scale(self._sx, self._sy))

    def scale_x(self) -> float: return self._sx
    def scale_y(self) -> float: return self._sy

    # ── Handle geometry (local item coordinates) ──────────────────────────

    def _hx(self) -> float:
        return self._H / max(0.01, self._sx)

    def _hy(self) -> float:
        return self._H / max(0.01, self._sy)

    def _handles(self) -> dict:
        w = self.pixmap().width()
        h = self.pixmap().height()
        hx, hy = self._hx(), self._hy()
        return {
            self._RIGHT:  QRectF(w - hx,       h / 2 - hy / 2, hx, hy),
            self._BOTTOM: QRectF(w / 2 - hx / 2, h - hy,       hx, hy),
            self._CORNER: QRectF(w - hx,        h - hy,         hx, hy),
        }

    def _hit(self, pos: QPointF):
        for name, rect in self._handles().items():
            if rect.contains(pos):
                return name
        return None

    # ── Drawing ───────────────────────────────────────────────────────────

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.save()
        pen_w = 2.0 / max(0.01, (self._sx + self._sy) / 2)
        painter.setPen(QPen(QColor("#ffffff"), pen_w))
        painter.setBrush(QColor("#2980b9"))
        for rect in self._handles().values():
            painter.drawRect(rect)
        painter.restore()

    # ── Hover cursor ──────────────────────────────────────────────────────

    def hoverMoveEvent(self, event):
        cursors = {
            self._RIGHT:  Qt.CursorShape.SizeHorCursor,
            self._BOTTOM: Qt.CursorShape.SizeVerCursor,
            self._CORNER: Qt.CursorShape.SizeFDiagCursor,
        }
        h = self._hit(event.pos())
        self.setCursor(cursors[h] if h else Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()

    # ── Mouse events ──────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        h = self._hit(event.pos()) if event.button() == Qt.MouseButton.LeftButton else None
        if h:
            self._active = h
            self._origin_scene = self.mapToScene(QPointF(0, 0))
            self._start_mouse = event.scenePos()
            self._start_sx = self._sx
            self._start_sy = self._sy
            event.accept()
        else:
            self._active = None
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._active is None:
            super().mouseMoveEvent(event)
            return

        d_now   = event.scenePos()    - self._origin_scene
        d_start = self._start_mouse   - self._origin_scene
        sx, sy  = self._sx, self._sy

        if self._active in (self._RIGHT, self._CORNER) and abs(d_start.x()) > 0.5:
            sx = max(0.1, min(5.0, self._start_sx * d_now.x() / d_start.x()))

        if self._active in (self._BOTTOM, self._CORNER) and abs(d_start.y()) > 0.5:
            sy = max(0.1, min(5.0, self._start_sy * d_now.y() / d_start.y()))

        self.set_scale_xy(sx, sy)
        if self.scale_x_changed_cb:
            self.scale_x_changed_cb(self._sx * 100.0)
        if self.scale_y_changed_cb:
            self.scale_y_changed_cb(self._sy * 100.0)
        event.accept()

    def mouseReleaseEvent(self, event):
        self._active = None
        super().mouseReleaseEvent(event)


class _AlignmentView(QGraphicsView):
    def __init__(self, ref_pixmap: QPixmap, overlay_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        scene = QGraphicsScene(self)
        self.setScene(scene)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)

        scene.addPixmap(ref_pixmap).setZValue(0)

        self._overlay = _ResizableOverlay(overlay_pixmap)
        scene.addItem(self._overlay)

        scene.setSceneRect(
            self._overlay.boundingRect().united(scene.items()[-1].boundingRect())
        )
        self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            step = 0.05 if event.angleDelta().y() > 0 else -0.05
            sx = self._overlay.scale_x() + step
            sy = self._overlay.scale_y() + step
            self._overlay.set_scale_xy(sx, sy)
            if self._overlay.scale_x_changed_cb:
                self._overlay.scale_x_changed_cb(self._overlay.scale_x() * 100.0)
            if self._overlay.scale_y_changed_cb:
                self._overlay.scale_y_changed_cb(self._overlay.scale_y() * 100.0)
        else:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)

    def set_overlay_scale_x(self, sx: float):
        self._overlay.set_scale_xy(sx, self._overlay.scale_y())

    def set_overlay_scale_y(self, sy: float):
        self._overlay.set_scale_xy(self._overlay.scale_x(), sy)

    def offset_px(self) -> tuple[float, float]:
        return self._overlay.x(), self._overlay.y()


class AlignmentDialog(QDialog):
    """
    Visual floor alignment tool (ADR-003).

    Drag the overlay to translate it.
    Drag the right handle  (↔) to adjust width independently.
    Drag the bottom handle (↕) to adjust height independently.
    Drag the corner handle (↘) to adjust both simultaneously.
    Scroll = zoom view · Ctrl+Scroll = uniform scale.
    """

    def __init__(
        self,
        ref_path: str,
        cur_path: str,
        ref_scale_px_per_m: float,
        cur_scale_px_per_m: float | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Recalage inter-étages")
        self.resize(960, 700)
        self._ref_scale = ref_scale_px_per_m

        ref_px = QPixmap(ref_path)
        cur_px = QPixmap(cur_path)

        if cur_scale_px_per_m and cur_scale_px_per_m > 0:
            ratio = ref_scale_px_per_m / cur_scale_px_per_m
            cur_px = cur_px.scaled(
                int(cur_px.width() * ratio),
                int(cur_px.height() * ratio),
                Qt.AspectRatioMode.IgnoreAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )

        layout = QVBoxLayout(self)

        info = QLabel(
            "Glisser l'overlay = déplacer  ·  "
            "Poignée droite (↔) = largeur  ·  "
            "Poignée bas (↕) = hauteur  ·  "
            "Coin (↘) = les deux  ·  "
            "Molette = zoom  ·  Ctrl+Molette = échelle uniforme."
        )
        info.setStyleSheet("color: #aaaaaa; padding: 4px;")
        info.setWordWrap(True)
        layout.addWidget(info)

        self._view = _AlignmentView(ref_px, cur_px)
        layout.addWidget(self._view, stretch=1)

        # Scale spinboxes
        scale_row = QHBoxLayout()

        scale_row.addWidget(QLabel("Largeur :"))
        self._spin_x = self._make_spin()
        self._spin_x.valueChanged.connect(
            lambda v: self._view.set_overlay_scale_x(v / 100.0)
        )
        scale_row.addWidget(self._spin_x)

        scale_row.addSpacing(16)
        scale_row.addWidget(QLabel("Hauteur :"))
        self._spin_y = self._make_spin()
        self._spin_y.valueChanged.connect(
            lambda v: self._view.set_overlay_scale_y(v / 100.0)
        )
        scale_row.addWidget(self._spin_y)

        reset_btn = QPushButton("Réinitialiser")
        reset_btn.clicked.connect(self._reset_scale)
        scale_row.addSpacing(16)
        scale_row.addWidget(reset_btn)
        scale_row.addStretch()
        layout.addLayout(scale_row)

        self._view._overlay.scale_x_changed_cb = self._sync_x
        self._view._overlay.scale_y_changed_cb = self._sync_y

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        cancel = QPushButton("Annuler")
        cancel.clicked.connect(self.reject)
        btn_row.addWidget(cancel)
        ok = QPushButton("Valider")
        ok.setDefault(True)
        ok.clicked.connect(self.accept)
        btn_row.addWidget(ok)
        layout.addLayout(btn_row)

    @staticmethod
    def _make_spin() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(10.0, 500.0)
        spin.setValue(100.0)
        spin.setSingleStep(5.0)
        spin.setSuffix(" %")
        spin.setFixedWidth(100)
        return spin

    def _reset_scale(self):
        self._spin_x.setValue(100.0)
        self._spin_y.setValue(100.0)

    def _sync_x(self, pct: float):
        self._spin_x.blockSignals(True)
        self._spin_x.setValue(pct)
        self._spin_x.blockSignals(False)

    def _sync_y(self, pct: float):
        self._spin_y.blockSignals(True)
        self._spin_y.setValue(pct)
        self._spin_y.blockSignals(False)

    def offset_m(self) -> tuple[float, float]:
        ox, oy = self._view.offset_px()
        return ox / self._ref_scale, oy / self._ref_scale
