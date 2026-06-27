import numpy as np


# Color stops: (dBm, R, G, B, A)
_STOPS = np.array([
    [-95, 180,  30,  30,   0],   # transparent — no signal
    [-88, 231,  76,  60, 190],   # red
    [-75, 243, 156,  18, 205],   # orange
    [-62, 241, 196,  15, 215],   # yellow
    [-50,  46, 204, 113, 220],   # green
    [-40,  52, 152, 219, 225],   # blue — excellent
], dtype=float)


def idw(points: list[tuple[float, float, float]],
        width_px: float, height_px: float,
        grid_size: int = 150, power: int = 2) -> np.ndarray:
    """
    Inverse Distance Weighting on a grid.

    points : list of (x_px, y_px, signal_dbm)
    Returns : (grid_size, grid_size) float array in dBm, NaN where undefined.
    """
    if not points:
        return np.full((grid_size, grid_size), np.nan)

    px = np.array([p[0] for p in points], dtype=float)
    py = np.array([p[1] for p in points], dtype=float)
    pv = np.array([p[2] for p in points], dtype=float)

    xs = np.linspace(0, width_px, grid_size)
    ys = np.linspace(0, height_px, grid_size)
    gx, gy = np.meshgrid(xs, ys)          # (G, G)

    # (G, G, N) distance arrays
    dx = gx[:, :, np.newaxis] - px
    dy = gy[:, :, np.newaxis] - py
    d2 = dx ** 2 + dy ** 2                 # (G, G, N)

    # Handle exact coincidences (d < 0.5 px)
    coincident = d2 < 0.25
    d2 = np.where(coincident, 1.0, d2)

    weights = 1.0 / (d2 ** (power / 2))   # (G, G, N)
    grid = (weights * pv).sum(axis=2) / weights.sum(axis=2)

    # Override exact matches with their direct value
    any_coin = coincident.any(axis=2)
    if any_coin.any():
        ii, jj = np.where(any_coin)
        for i, j in zip(ii, jj):
            k = int(np.argmin(d2[i, j]))
            grid[i, j] = pv[k]

    return grid


def idw_points(
    source: list[tuple[float, float, float]],
    queries: list[tuple[float, float]],
    power: int = 2,
) -> np.ndarray:
    """IDW at arbitrary (x, y) query positions. Returns 1D float array (dBm)."""
    if not source or not queries:
        return np.full(len(queries), np.nan)

    sx = np.array([p[0] for p in source], dtype=float)
    sy = np.array([p[1] for p in source], dtype=float)
    sv = np.array([p[2] for p in source], dtype=float)
    qx = np.array([q[0] for q in queries], dtype=float)
    qy = np.array([q[1] for q in queries], dtype=float)

    dx = qx[:, np.newaxis] - sx   # (Q, S)
    dy = qy[:, np.newaxis] - sy
    d2 = dx ** 2 + dy ** 2

    coincident = d2 < 0.25
    d2 = np.where(coincident, 1.0, d2)
    weights = 1.0 / (d2 ** (power / 2))
    result = (weights * sv).sum(axis=1) / weights.sum(axis=1)

    any_coin = coincident.any(axis=1)
    if any_coin.any():
        for i in np.where(any_coin)[0]:
            result[i] = sv[int(np.argmin(d2[i]))]

    return result


def grid_to_rgba(grid: np.ndarray) -> np.ndarray:
    """
    Map a (H, W) dBm grid to a (H, W, 4) RGBA uint8 array.
    NaN or values below the lowest stop → transparent (alpha=0).
    """
    H, W = grid.shape
    flat = grid.ravel()                    # (N,)
    threshold = _STOPS[0, 0]

    valid = ~np.isnan(flat) & (flat >= threshold)
    clamped = np.clip(flat, _STOPS[0, 0], _STOPS[-1, 0])

    # Interval index for each pixel
    k = np.searchsorted(_STOPS[:, 0], clamped, side="right") - 1
    k = np.clip(k, 0, len(_STOPS) - 2)

    denom = _STOPS[k + 1, 0] - _STOPS[k, 0]
    t = (clamped - _STOPS[k, 0]) / np.where(denom > 0, denom, 1.0)
    t = np.clip(t, 0.0, 1.0)[:, np.newaxis]   # (N, 1)

    colors = _STOPS[k, 1:] + t * (_STOPS[k + 1, 1:] - _STOPS[k, 1:])
    colors = np.clip(colors, 0, 255).astype(np.uint8)
    colors[~valid] = 0                     # transparent for invalid pixels

    return colors.reshape(H, W, 4)
