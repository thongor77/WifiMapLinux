from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QDoubleSpinBox, QGraphicsItem, QGraphicsScene, QGraphicsView,
    QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)


class _AlignmentView(QGraphicsView):
    def __init__(self, ref_pixmap: QPixmap, overlay_pixmap: QPixmap, parent=None):
        super().__init__(parent)
        scene = QGraphicsScene(self)
        self.setScene(scene)
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setRenderHint(self.renderHints())
        self._scale_changed_cb = None

        # Reference floor: full opacity, not movable
        scene.addPixmap(ref_pixmap).setZValue(0)

        # Current floor: semi-transparent, draggable
        self._overlay = scene.addPixmap(overlay_pixmap)
        self._overlay.setZValue(1)
        self._overlay.setOpacity(0.5)
        self._overlay.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)
        self._overlay.setTransformOriginPoint(0, 0)

        scene.setSceneRect(self._overlay.boundingRect().united(
            scene.items()[-1].boundingRect()
        ))
        self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Ctrl+wheel → scale the overlay
            delta = event.angleDelta().y()
            step = 0.05 if delta > 0 else -0.05
            new_scale = max(0.1, min(5.0, self._overlay.scale() + step))
            self._overlay.setScale(new_scale)
            if self._scale_changed_cb:
                self._scale_changed_cb(new_scale * 100.0)
        else:
            factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
            self.scale(factor, factor)

    def set_scale_changed_callback(self, cb):
        self._scale_changed_cb = cb

    def set_overlay_scale(self, factor: float):
        self._overlay.setScale(factor)

    def offset_px(self) -> tuple[float, float]:
        return self._overlay.x(), self._overlay.y()


class AlignmentDialog(QDialog):
    """
    Visual floor alignment tool (ADR-003).

    Displays the reference floor (full opacity) and the current floor
    (semi-transparent, draggable) so the user can align them by dragging.
    Wheel-zooms for precision. Saving stores the pixel offset converted to metres.
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

        # Scale overlay to match reference coordinate system when both calibrated
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
            "Glissez l'étage supérieur (semi-transparent) pour l'aligner "
            "sur le plan de référence.  "
            "Molette = zoom vue  ·  Ctrl+Molette = échelle overlay."
        )
        info.setStyleSheet("color: #aaaaaa; padding: 4px;")
        layout.addWidget(info)

        self._view = _AlignmentView(ref_px, cur_px)
        layout.addWidget(self._view, stretch=1)

        # Scale control row
        scale_row = QHBoxLayout()
        scale_lbl = QLabel("Échelle overlay :")
        scale_row.addWidget(scale_lbl)
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

        self._view.set_scale_changed_callback(self._sync_scale_spin)

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
