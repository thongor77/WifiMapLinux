from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog, QGraphicsItem, QGraphicsScene, QGraphicsView,
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

        # Reference floor: full opacity, not movable
        scene.addPixmap(ref_pixmap).setZValue(0)

        # Current floor: semi-transparent, draggable
        self._overlay = scene.addPixmap(overlay_pixmap)
        self._overlay.setZValue(1)
        self._overlay.setOpacity(0.5)
        self._overlay.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable)

        scene.setSceneRect(self._overlay.boundingRect().united(
            scene.items()[-1].boundingRect()
        ))
        self.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self.scale(factor, factor)

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
            "sur le plan de référence. Molette = zoom."
        )
        info.setStyleSheet("color: #aaaaaa; padding: 4px;")
        layout.addWidget(info)

        self._view = _AlignmentView(ref_px, cur_px)
        layout.addWidget(self._view, stretch=1)

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

    def offset_m(self) -> tuple[float, float]:
        """Return (offset_x_m, offset_y_m) in the reference floor's coordinate system."""
        ox, oy = self._view.offset_px()
        return ox / self._ref_scale, oy / self._ref_scale
