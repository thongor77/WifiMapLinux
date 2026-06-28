import numpy as np
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QStackedWidget, QVBoxLayout, QWidget

from ..services.i18n import tr
from ..services.interpolation import _STOPS

_PLAN_TEX = 256   # floor plan texture resolution (px)


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


def _load_plan_texture(image_path: str) -> np.ndarray | None:
    """
    Load a floor plan PNG as a (_PLAN_TEX, _PLAN_TEX, 4) RGBA uint8 array.
    Near-white pixels (background) are made transparent; dark pixels (walls)
    are kept at alpha=180 so the plan reads through the volume.
    """
    try:
        from PIL import Image as PILImage
        img = PILImage.open(image_path).convert('RGBA')
        img = img.resize((_PLAN_TEX, _PLAN_TEX), PILImage.LANCZOS)
        arr = np.array(img, dtype=np.uint8)
        white = (arr[:, :, 0] > 210) & (arr[:, :, 1] > 210) & (arr[:, :, 2] > 210)
        arr[:, :, 3] = np.where(white, 0, 180)
        # vispy Image maps row 0 → Y=0 (bottom of scene), so flip to keep top↑
        return np.ascontiguousarray(arr[::-1])
    except Exception:
        return None


class VoxelView(QWidget):
    """3D voxel volume view — vispy SceneCanvas embedded in a QWidget."""

    _GRID_SIZE = 150
    _Z_RESOLUTION = 40

    def __init__(self, parent=None):
        super().__init__(parent)
        self._canvas = None
        self._view = None
        self._volume_visual = None
        self._floor_plan_visuals: list = []
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

    def _clear_floor_plans(self):
        for vis in self._floor_plan_visuals:
            vis.parent = None
        self._floor_plan_visuals = []

    def set_volume(self, voxels: np.ndarray, z_total_m: float,
                   floor_plans: list[tuple[str | None, float]] | None = None):
        """
        Render the (Z, G, G) dBm volume.

        floor_plans: list of (image_path | None, z_mid_frac) ordered
                     bottom→top. z_mid_frac is the floor's vertical midpoint
                     as a fraction of z_total_m (0 = ground, 1 = top).
        """
        if self._canvas is None:
            return

        import vispy.scene
        from vispy.scene.visuals import Image as VispyImage, Volume
        from vispy.visuals.transforms import STTransform

        Z, G, _ = voxels.shape

        # ── Volume ───────────────────────────────────────────────────────────
        dbm_min, dbm_max = float(_STOPS[0, 0]), float(_STOPS[-1, 0])
        norm = np.clip((voxels - dbm_min) / (dbm_max - dbm_min), 0.0, 1.0)
        norm = np.where(np.isnan(voxels), 0.0, norm).astype(np.float32)

        # Flip Z: index 0 = bottom (RDC), index Z-1 = top
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

        # Scale Z so the visual height matches the XY extent (cube aspect)
        z_scale = G / Z if Z > 0 else 1.0
        self._volume_visual.transform = STTransform(scale=(1.0, 1.0, z_scale))

        # ── Floor plan projections ────────────────────────────────────────────
        self._clear_floor_plans()
        scale_xy = G / _PLAN_TEX   # maps texture pixels → volume XY units

        for image_path, z_mid_frac in (floor_plans or []):
            if not image_path:
                continue
            tex = _load_plan_texture(image_path)
            if tex is None:
                continue

            # method='subdivide' tessellates the quad → perspective-correct in 3D
            img_vis = VispyImage(tex, method='subdivide', parent=self._view.scene)
            # Alpha blend, no depth write, double-sided so the plane is
            # visible regardless of camera orientation.
            img_vis.set_gl_state('translucent', depth_test=False, cull_face=False)

            # The volume after STTransform spans Z ∈ [0, G].
            # The plan at z_mid_frac sits at Z_world = z_mid_frac * G.
            z_world = z_mid_frac * G
            img_vis.transform = STTransform(
                scale=(scale_xy, scale_xy, 1.0),
                translate=(0.0, 0.0, z_world),
            )
            self._floor_plan_visuals.append(img_vis)

        self._view.camera.set_range()
        self._stack.setCurrentIndex(1)

    def clear(self):
        if self._volume_visual is not None:
            self._volume_visual.parent = None
            self._volume_visual = None
        self._clear_floor_plans()
        self._show_empty()
