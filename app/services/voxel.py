import numpy as np


def build_voxel_grid(
    floor_grids: list,
    floor_heights_m: list[float],
    z_resolution: int = 40,
    grid_size: int = 150,
) -> tuple[np.ndarray, float]:
    """
    Build a (Z, G, G) voxel array from per-floor 2D grids.

    floor_grids: ordered bottom→top list of (G, G) dBm arrays or None.
    floor_heights_m: floor heights in metres (same order).
    Returns (voxels, z_total_m). voxels[0] = top, voxels[-1] = bottom.

    Vertical interpolation follows the same searchsorted-lerp pattern as
    SectionView._build_interpolated (ADR-006): each floor contributes one
    representative slice at its vertical midpoint; slices between midpoints
    are linearly blended; values beyond the outermost data floors are clamped.
    """
    z_total_m = sum(floor_heights_m)
    if z_total_m <= 0:
        return np.full((z_resolution, grid_size, grid_size), np.nan), 0.0

    data_floors: list[tuple[float, np.ndarray]] = []
    z = 0.0
    for grid, h_m in zip(floor_grids, floor_heights_m):
        if grid is not None and not np.all(np.isnan(grid)):
            z_mid_frac = (z + h_m / 2.0) / z_total_m
            data_floors.append((z_mid_frac, np.asarray(grid, dtype=float)))
        z += h_m

    if not data_floors:
        return np.full((z_resolution, grid_size, grid_size), np.nan), z_total_m

    z_pts = np.array([zf for zf, _ in data_floors])     # (D,)
    grids_arr = np.array([g for _, g in data_floors])    # (D, G, G)

    # row 0 → top (z_frac=1.0), row Z-1 → bottom (z_frac=0.0)
    z_fracs = np.linspace(1.0, 0.0, z_resolution)       # (Z,)

    if len(data_floors) == 1:
        return np.broadcast_to(grids_arr[0], (z_resolution, grid_size, grid_size)).copy(), z_total_m

    k = np.searchsorted(z_pts, z_fracs, side='right') - 1
    k = np.clip(k, 0, len(z_pts) - 2)

    z0 = z_pts[k]
    z1 = z_pts[k + 1]
    dz = z1 - z0
    t = np.where(dz > 0, (z_fracs - z0) / dz, 0.0)
    t = np.clip(t, 0.0, 1.0)[:, np.newaxis, np.newaxis]  # (Z, 1, 1)

    voxels = grids_arr[k] + t * (grids_arr[k + 1] - grids_arr[k])   # (Z, G, G)
    return voxels, z_total_m
