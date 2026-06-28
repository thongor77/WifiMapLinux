import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from ..services.i18n import tr
from ..services.interpolation import _STOPS


def _build_vispy_colormap():
    """Build a vispy Colormap matching the 2D heatmap palette (_STOPS)."""
    from vispy.color import ColorArray, Colormap
    dbm_min, dbm_max = float(_STOPS[0, 0]), float(_STOPS[-1, 0])
    span = dbm_max - dbm_min
    positions = [(_STOPS[i, 0] - dbm_min) / span for i in range(len(_STOPS))]
    colors_rgba = [
        [_STOPS[i, 1] / 255, _STOPS[i, 2] / 255, _STOPS[i, 3] / 255, _STOPS[i, 4] / 255]
        for i in range(len(_STOPS))
    ]
    return Colormap(colors=ColorArray(color=colors_rgba), controls=positions)


class VoxelView(QWidget):
    """3D voxel volume view — vispy SceneCanvas embedded in a QWidget."""

    _GRID_SIZE = 150
    _Z_RESOLUTION = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self._canvas = None
        self._view = None
        self._volume_visual = None
        self._colormap = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._stack = QStackedWidget()
        outer.addWidget(self._stack)

        # Page 0: empty state
        self._empty_label = QLabel()
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setStyleSheet(
            "color: #555577; font-size: 9pt; background: #1e1e2e;"
        )
        self._stack.addWidget(self._empty_label)

        # Page 1: vispy canvas (or error label)
        try:
            import vispy.scene
            from vispy.app import use_app
            use_app('pyside6')

            self._canvas = vispy.scene.SceneCanvas(
                keys='interactive', bgcolor='#1e1e2e', show=False
            )
            self._view = self._canvas.central_widget.add_view()
            self._view.camera = vispy.scene.cameras.TurntableCamera(
                fov=40, elevation=20, azimuth=-60
            )
            self._colormap = _build_vispy_colormap()
            self._stack.addWidget(self._canvas.native)
        except Exception as exc:
            err = QLabel(f"vispy unavailable: {exc}")
            err.setAlignment(Qt.AlignmentFlag.AlignCenter)
            err.setStyleSheet("color: #cc3333; background: #1e1e2e;")
            self._stack.addWidget(err)

        self._show_empty()

    def _show_empty(self):
        self._empty_label.setText(tr("voxel_empty"))
        self._stack.setCurrentIndex(0)

    def set_volume(self, voxels: np.ndarray, z_total_m: float):
        """Render the (Z, G, G) dBm volume. Noop if vispy canvas failed."""
        if self._canvas is None:
            return

        import vispy.scene
        from vispy.scene.visuals import Volume
        from vispy.visuals.transforms import STTransform

        Z, G, _ = voxels.shape

        # Normalise dBm → [0, 1] for the colormap
        dbm_min, dbm_max = float(_STOPS[0, 0]), float(_STOPS[-1, 0])
        norm = np.clip((voxels - dbm_min) / (dbm_max - dbm_min), 0.0, 1.0)
        norm = np.where(np.isnan(voxels), 0.0, norm).astype(np.float32)

        # Flip Z: index 0 = bottom of building for natural orientation
        vol_data = norm[::-1].copy()

        if self._volume_visual is not None:
            self._volume_visual.parent = None

        self._volume_visual = Volume(
            vol_data,
            clim=(0.0, 1.0),
            method='translucent',
            cmap=self._colormap,
            parent=self._view.scene,
        )

        # Scale Z so the volume looks physically proportional:
        # make Z axis span the same visual units as the XY axis.
        z_scale = G / Z if Z > 0 else 1.0
        self._volume_visual.transform = STTransform(scale=(1.0, 1.0, z_scale))

        self._view.camera.set_range()
        self._stack.setCurrentIndex(1)

    def clear(self):
        if self._volume_visual is not None:
            self._volume_visual.parent = None
            self._volume_visual = None
        self._show_empty()
