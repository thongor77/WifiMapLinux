import numpy as np
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QColor, QFont, QImage, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ..services.interpolation import grid_to_rgba


class SectionView(QWidget):
    """
    Cross-section view (V1.5 + V2.2).
    Horizontal axis = distance in metres along the section line.
    Vertical axis   = floors stacked from bottom (index 0) to top.
    Colour          = RSSI using the same palette as the heatmap.

    V2.2 (ADR-006): linear interpolation between floor midpoints replaces
    hard-edged bands. The interpolated image is rendered in a single pass;
    floor separators and labels are drawn on top.
    """

    _LABEL_W = 74
    _AXIS_H = 22
    _PAD_T = 6
    _PAD_R = 8
    _N = 200   # horizontal samples — must match _refresh_section N in main_window

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(100)
        # Each band: (label: str, height_m: float, rssi_1d: np.ndarray | None)
        # Ordered bottom-to-top (lowest floor index first).
        self._bands: list = []
        self._line_length_m: float = 0.0

    def update_section(self, bands: list, line_length_m: float) -> None:
        self._bands = bands
        self._line_length_m = line_length_m
        self.update()

    # ── Interpolation ─────────────────────────────────────────────────────

    def _build_interpolated(self, ch: int, total_h_m: float) -> np.ndarray | None:
        """
        Build a (ch, N) dBm grid by linear interpolation between floor midpoints.

        Each floor contributes one representative RSSI row at its vertical midpoint.
        Values between midpoints are linearly blended; values beyond the outermost
        data floors are clamped to the nearest floor's RSSI (no extrapolation).

        Returns None when no floor has measurement data.
        Pixel row 0 = top of section, row ch-1 = bottom.
        """
        data_floors: list[tuple[float, np.ndarray]] = []
        z = 0.0
        N = self._N
        for _, h_m, rssi in self._bands:
            if rssi is not None and len(rssi) > 0:
                z_mid_frac = (z + h_m / 2.0) / total_h_m
                arr = np.asarray(rssi, dtype=float)
                if len(arr) != N:
                    x_old = np.linspace(0.0, 1.0, len(arr))
                    x_new = np.linspace(0.0, 1.0, N)
                    arr = np.interp(x_new, x_old, arr)
                data_floors.append((z_mid_frac, arr))
            z += h_m

        if not data_floors:
            return None

        z_pts = np.array([zf for zf, _ in data_floors])    # (D,) ascending
        rssi_m = np.array([arr for _, arr in data_floors])  # (D, N)

        # Pixel rows: row 0 → z_frac=1.0 (top), row ch-1 → z_frac=0.0 (bottom)
        z_fracs = np.linspace(1.0, 0.0, ch)   # (ch,)

        if len(data_floors) == 1:
            return np.tile(rssi_m[0], (ch, 1))

        # Vectorised lerp — searchsorted gives the right-interval index
        k = np.searchsorted(z_pts, z_fracs, side='right') - 1
        k = np.clip(k, 0, len(z_pts) - 2)

        z0 = z_pts[k]
        z1 = z_pts[k + 1]
        dz = z1 - z0
        t = np.where(dz > 0, (z_fracs - z0) / dz, 0.0)
        t = np.clip(t, 0.0, 1.0)[:, np.newaxis]   # (ch, 1)

        return rssi_m[k] + t * (rssi_m[k + 1] - rssi_m[k])   # (ch, N)

    # ── Painting ──────────────────────────────────────────────────────────

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        W, H = self.width(), self.height()

        p.fillRect(0, 0, W, H, QColor("#1e1e2e"))

        cw = W - self._LABEL_W - self._PAD_R
        ch = H - self._PAD_T - self._AXIS_H

        if not self._bands or self._line_length_m < 0.01 or cw < 20 or ch < 20:
            font = QFont()
            font.setPointSize(9)
            p.setFont(font)
            p.setPen(QColor("#555577"))
            p.drawText(0, 0, W, H, Qt.AlignmentFlag.AlignCenter,
                       "Tracez une ligne de coupe sur le plan")
            return

        total_h_m = sum(b[1] for b in self._bands)
        if total_h_m <= 0:
            return

        # Background
        p.fillRect(self._LABEL_W, self._PAD_T, cw, ch, QColor("#252535"))

        # Interpolated RSSI image (V2.2 — replaces per-band solid rects)
        grid = self._build_interpolated(ch, total_h_m)
        if grid is not None:
            rgba = grid_to_rgba(grid).copy()
            rgba[:, :, 3] = np.where(rgba[:, :, 3] > 0, 210, 0)
            img = QImage(
                rgba.tobytes(), self._N, ch, 4 * self._N,
                QImage.Format.Format_RGBA8888,
            )
            p.drawImage(QRect(self._LABEL_W, self._PAD_T, cw, ch), img)

        # Floor separators and labels
        z = 0.0
        for label, h_m, rssi in self._bands:
            y_bottom = self._PAD_T + ch - int(z / total_h_m * ch)
            y_top    = self._PAD_T + ch - int((z + h_m) / total_h_m * ch)
            band_h   = max(1, y_bottom - y_top)

            # Hatch only for floors with no data AND outside the interpolated range
            if rssi is None:
                pen = QPen(QColor("#38385a"), 1, Qt.PenStyle.DotLine)
                p.setPen(pen)
                for xi in range(0, cw + 16, 16):
                    p.drawLine(self._LABEL_W + xi, y_top,
                               self._LABEL_W + xi, y_bottom)

            if z > 0:
                p.setPen(QPen(QColor("#cccccc"), 1))
                p.drawLine(self._LABEL_W, y_bottom, W - self._PAD_R, y_bottom)

            font = QFont()
            font.setPointSize(8)
            p.setFont(font)
            p.setPen(QColor("#bbbbcc"))
            p.drawText(
                QRect(2, y_top, self._LABEL_W - 6, band_h),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                label,
            )

            z += h_m

        # Content border
        p.setPen(QPen(QColor("#444466"), 1))
        p.drawRect(self._LABEL_W, self._PAD_T, cw - 1, ch - 1)

        # X-axis ticks
        font = QFont()
        font.setPointSize(7)
        p.setFont(font)
        p.setPen(QColor("#778899"))
        n_ticks = min(8, max(2, int(self._line_length_m)))
        y_base = self._PAD_T + ch
        for i in range(n_ticks + 1):
            dist_m = self._line_length_m * i / n_ticks
            x_px   = self._LABEL_W + int(dist_m / self._line_length_m * cw)
            p.drawLine(x_px, y_base, x_px, y_base + 3)
            p.drawText(x_px - 14, y_base + 4, 28, self._AXIS_H - 5,
                       Qt.AlignmentFlag.AlignCenter, f"{dist_m:.1f}m")
