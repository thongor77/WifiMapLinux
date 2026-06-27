import math
from dataclasses import dataclass

import numpy as np

# ITU-R P.1238 — residential indoor path loss exponent
PATH_LOSS_EXPONENT = 3.0


@dataclass
class APSimInfo:
    bx_m: float        # AP position in building coords (metres)
    by_m: float
    z_m: float         # AP height from ground (metres)
    floor_index: int   # Floor.index — used to count crossed slabs
    tx_dbm: float
    freq_mhz: float
    faf_db: float      # Floor attenuation per slab (ADR-004)


def _fspl_1m_db(freq_mhz: float) -> float:
    """Free-space path loss at 1 m reference distance (dB)."""
    return 20.0 * math.log10(4.0 * math.pi * freq_mhz * 1e6 / 3e8)


def simulate_floor(
    aps: list[APSimInfo],
    target_floor_index: int,
    target_z_m: float,
    target_boffset_x: float,
    target_boffset_y: float,
    target_scale: float,      # px/m of target floor plan
    fp_width_px: int,
    fp_height_px: int,
    grid_size: int = 150,
) -> np.ndarray:
    """
    Log-Distance Path Loss 3D simulation for one floor.

    Combines signal from all APs (best signal wins per cell).
    Returns a (grid_size, grid_size) float array in dBm.
    NaN when no APs are provided.
    """
    if not aps:
        return np.full((grid_size, grid_size), np.nan)

    xs = np.linspace(0.0, float(fp_width_px), grid_size)
    ys = np.linspace(0.0, float(fp_height_px), grid_size)
    gx, gy = np.meshgrid(xs, ys)   # (G, G) pixel coords on target floor plan

    # Grid cells in building coordinates (metres)
    gbx = target_boffset_x + gx / target_scale
    gby = target_boffset_y + gy / target_scale

    best = np.full((grid_size, grid_size), -300.0)

    for ap in aps:
        n_floors = abs(ap.floor_index - target_floor_index)
        dz = abs(target_z_m - ap.z_m)
        dx = gbx - ap.bx_m
        dy = gby - ap.by_m
        # 3D distance, minimum 0.5 m to avoid log(0)
        d_3d = np.maximum(np.sqrt(dx**2 + dy**2 + dz**2), 0.5)
        pl = (
            _fspl_1m_db(ap.freq_mhz)
            + 10.0 * PATH_LOSS_EXPONENT * np.log10(d_3d)
            + ap.faf_db * n_floors
        )
        best = np.maximum(best, ap.tx_dbm - pl)

    return best
