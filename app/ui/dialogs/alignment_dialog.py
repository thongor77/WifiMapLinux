import math

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QPen, QPixmap
from PySide6.QtWidgets import (
    QDialog, QDoubleSpinBox, QGraphicsItem, QGraphicsPixmapItem,
    QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


class _ResizableOverlay(QGraphicsPixmapItem):
    """
    Semi-transparent overlay that can be dragged (anywhere) or scaled
    by dragging the blue handle at the bottom-right corner.
    """

    _HANDLE_PX = 14  # handle size in screen pixels, compensated for item scale

    def __init__(self, pixmap: QPixmap):
        super().__init__(pixmap)
        self.setOpacity(0.5)
        self.setZValue(1)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self.setAcceptHoverEvents(True)
        self.setTransformOriginPoint(0, 0)
        self._resizing = False
        self._origin_scene = QPointF()
        self._start_scale = 1.0
        self._start_dist = 1.0
        self.scale_changed_cb = None

    # ── Handle geometry ───────────────────────────────────────────────────

    def _local_handle_size(self) -> float:
        return self._HANDLE_PX / max(0.01, self.scale())

    def _handle_rect(self) -> QRectF:
        s = self._local_handle_size()
        w, h = self.pixmap().width(), self.pixmap().height()
        return QRectF(w - s, h - s, s, s)

    # ── Drawing ───────────────────────────────────────────────────────────

    def paint(self, painter, option, widget=None):
        super().paint(painter, option, widget)
        painter.save()
        pen_w = 2.0 / max(0.01, self.scale())
        painter.setPen(QPen(QColor("#ffffff"), pen_w))
        painter.setBrush(QColor("#2980b9"))
        painter.drawRect(self._handle_rect())
        painter.restore()

    # ── Hover: cursor feedback ────────────────────────────────────────────

    def hoverMoveEvent(self, event):
        if self._handle_rect().contains(event.pos()):
            self.setCursor(Qt.CursorShape.SizeFDiagCursor)
        else:
            self.setCursor(Qt.CursorShape.SizeAllCursor)

    def hoverLeaveEvent(self, event):
        self.unsetCursor()

    # ── Mouse: drag vs. resize ────────────────────────────────────────────

    def mousePressEvent(self, event):
        if (event.button() == Qt.MouseButton.LeftButton
                and self._handle_rect().contains(event.pos())):
            self._resizing = True
            self._origin_scene = self.mapToScene(QPointF(0, 0))
            self._start_scale = self.scale()
            d = event.scenePos() - self._origin_scene
            self._start_dist = math.hypot(d.x(), d.y())
            event.accept()
        else:
            self._resizing = False
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._resizing:
            d = event.scenePos() - self._origin_scene
            dist = math.hypot(d.x(), d.y())
            if self._start_dist > 0.5:
                new_scale = max(0.1, min(5.0,
                                         self._start_scale * dist / self._start_dist))
                self.setScale(new_scale)
                if self.scale_changed_cb:
                    self.scale_changed_cb(new_scale * 100.0)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self._resizing = False
        super().mouseReleaseEvent(event)


class _AlignmentView(QGraphicsView):
    def __init__(self, ref_pixmap: QPixmap, overlay_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        scene = QGraphicsScene(self)
        self.setScene(scene)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(self.renderHints())

        # Reference floor: full opacity, fixed
        scene.addPixmap(ref_pixmap).setZValue(0)

        # Current floor: semi-transparent, draggable + resizable
        self._overlay = _ResizableOverlay(overlay_pixmap)
        scene.addItem(self._overlay)

        scene.setSceneRect(
            self._overlay.boundingRect().united(scene.items()[-1].boundingRect())
        )
        self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            step = 0.05 if delta > 0 else -0.05
            new_scale = max(0.1, min(5.0, self._overlay.scale() + step))
            self._overlay.setScale(new_scale)
            if self._overlay.scale_changed_cb:
                self._overlay.scale_changed_cb(new_scale * 100.0)
        else:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)

    def set_overlay_scale(self, factor: float):
        self._overlay.setScale(factor)

    def offset_px(self) -> tuple[float, float]:
        return self._overlay.x(), self._overlay.y()


class AlignmentDialog(QDialog):
    """
    Visual floor alignment tool (ADR-003).

    Reference floor at full opacity; current floor semi-transparent.
    — Drag anywhere on the overlay to translate it.
    — Drag the blue handle (bottom-right corner) to scale it uniformly.
    — Ctrl+Scroll or the spinbox for fine scale adjustment.
    — Regular scroll zooms the view for precision.
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
        self.resize(960, 680)
        self._ref_scale = ref_scale_px_per_m

        ref_px = QPixmap(ref_path)
        cur_px = QPixmap(cur_path)

        # Pre-scale overlay to match reference coordinate system when both calibrated
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
            "Glissez l'overlay pour le déplacer  ·  "
            "Glissez le coin bleu  pour le redimensionner  ·  "
            "Molette = zoom vue  ·  Ctrl+Molette = échelle."
        )
        info.setStyleSheet("color: #aaaaaa; padding: 4px;")
        layout.addWidget(info)

        self._view = _AlignmentView(ref_px, cur_px)
        layout.addWidget(self._view, stretch=1)

        # Scale control row
        scale_row = QHBoxLayout()
        scale_row.addWidget(QLabel("Échelle overlay :"))
        self._scale_spin = QDoubleSpinBox()
        self._scale_spin.setRange(10.0, 500.0)
        self._scale_spin.setValue(100.0)
        self._scale_spin.setSingleStep(5.0)
        self._scale_spin.setSuffix(" %")
        self._scale_spin.setFixedWidth(100)
        self._scale_spin.valueChanged.connect(
            lambda v: self._view.set_overlay_scale(v / 100.0)
        )
        scale_row.addWidget(self._scale_spin)
        reset_btn = QPushButton("Réinitialiser")
        reset_btn.clicked.connect(lambda: self._scale_spin.setValue(100.0))
        scale_row.addWidget(reset_btn)
        scale_row.addStretch()
        layout.addLayout(scale_row)

        self._view._overlay.scale_changed_cb = self._sync_scale_spin

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

    def _sync_scale_spin(self, pct: float):
        self._scale_spin.blockSignals(True)
        self._scale_spin.setValue(pct)
        self._scale_spin.blockSignals(False)

    def offset_m(self) -> tuple[float, float]:
        """Return (offset_x_m, offset_y_m) in the reference floor's coordinate system."""
        ox, oy = self._view.offset_px()
        return ox / self._ref_scale, oy / self._ref_scale
