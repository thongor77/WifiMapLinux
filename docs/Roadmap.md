# WifiMapLinux — Roadmap

> Last updated: 2026-06-27
> V2 complete.

---

## Overview

| Version | Scope | Status |
|---------|-------|--------|
| **Arch phase** | Architecture, data models, technical decisions | ✅ Done |
| **V1** | Floor plan import · Wi-Fi measurements · 2D heatmap · Multi-floor · Vertical section | ✅ Done |
| **V2** | Simulation · Advanced interpolation · Export | ✅ Done |
| **V3** | 3D visualisation | ✅ Done |
| **Post-V3** | AP placement advisor · PyInstaller packaging | 💭 Deferred |

---

## V1 — Functional application

Goal: user can measure Wi-Fi coverage across a multi-floor house
and view results as a 2D heatmap + vertical cross-section.

### V1.1 — Floor plan import ✅

### V1.2 — Wi-Fi measurements ✅

### V1.3 — 2D heatmap ✅

### V1.4 — Multi-floor ✅

### V1.5 — Vertical cross-section ✅

- 2-click cut line on the floor plan (dashed yellow)
- `SectionView` below the plan: per-floor RSSI-coloured bands, distance axis in metres
- Auto-refresh on measurement change or SSID filter change

---

## V2 — Enrichment

### V2.1 — Simulation ✅

- Virtual AP placement on floor plans (`AccessPoint` in SQLite)
- Log-Distance Path Loss 3D model — `app/services/propagation.py` (ITU-R P.1238, n=3.0, per-floor FAF from ADR-004)
- Simulated heatmap per floor (same rendering as V1.3, layer z=4 below measured heatmap z=5)
- Simulation / measured overlay: "Simulation" toggle independent of "Heatmap" toggle

### V2.2 — Advanced interpolation ✅

INC-04 resolved → ADR-006: Option A (per-floor 2D IDW + vertical linear interpolation).
- `SectionView` rebuilt: 2D image (ch × N) built by vectorised lerp between floor midpoints
- Floor transitions are now continuous gradients (no more hard bands)
- A floor without measurements is traversed by interpolation between its neighbours
- Per-floor 2D IDW unchanged (floor plan heatmap remains independent per floor)

### V2.3 — Export ✅

- PNG export: annotated plan + heatmap overlay (Pillow) — Export menu › PNG (Ctrl+E)
  - Exports the active heatmap (measured or simulated depending on toggles)
  - Banner: house, floor, SSID, RSSI stats, date
- PDF export: multi-page coverage report — Export menu › PDF (Ctrl+Shift+E)
  - Summary page: per-floor table (measurement points, RSSI min/avg/max)
  - One page per floor: plan + measured heatmap + banner
  - Generated with Pillow (1200 px/page, 150 DPI)

---

## V3 — 3D visualisation ✅

Technology: **vispy** (OpenGL Python, PySide6 backend).

Implemented:
- `app/services/voxel.py` — `build_voxel_grid()`: stacks per-floor 2D IDW/LDPL grids
  into a `(Z=40, G=150, G=150)` voxel volume with vertical lerp between floor midpoints
  (same ADR-006 algorithm as SectionView).
- `app/ui/voxel_view.py` — `VoxelView`: vispy SceneCanvas + TurntableCamera embedded in
  a QWidget; `scene.visuals.Volume` with `method='translucent'`; colormap matches the 2D
  heatmap palette (`_STOPS`).
- Bascule 2D↔3D via `QStackedWidget` in MainWindow; "3D View" checkbox in HeatmapControls.
- Sources: measured (IDW) or simulated (LDPL) — follows the Heatmap/Simulation toggles.
- Navigation: mouse rotation (TurntableCamera), scroll zoom.
- Known limitation: inter-floor XY alignment offsets are not applied to the voxel grid
  (floors assumed co-registered). Use the vertical section view for precise cross-floor analysis.

---

## Post-V3 (deferred)

- **AP placement advisor**: weak zone detection, clustering, position recommendation (threshold from ADR-005)
- **Packaging**: PyInstaller → single Linux binary
- **SVG export**: floor plan import with automatic wall detection
- **Rust module (PyO3)**: if performance is needed for propagation/interpolation
- **Router/box model selector**: let the user pick their actual device in the AP dialog;
  `effective_pire_dbm` (Tx + antenna gain) from the router DB replaces the generic
  `tx_power_dbm` in the LDPL simulation. Data source: `docs/Src/wifi_routers_db.json`
  (26 devices, WiFi 5–7, FR ISP boxes included). Confidence disclaimer required in the UI
  (most values are `estimated`, not `verified`). Standard "Generic" preset preserved as default.
  Extend the DB with non-mesh WiFi repeaters (TP-Link RE series, Netgear EX series, ISP
  repeaters) as a new `category: "repeater"`. In the AP placement dialog, add a mode toggle:
  **Répéteur WiFi** (applies ~-4 dB penalty to PIRE — half-duplex reception loss) vs
  **Mode AP câblé** (full nominal PIRE). Mesh nodes already in DB require no penalty.
- **i18n**: multi-language UI (FR/EN minimum) — reference implementation: `~/claude-projects/nmlinux/`
- **Help system**: contextual help or integrated documentation — reference: nmlinux
- **About dialog**: version number, author, project links — ✅ Done (v2.0+)
- **i18n**: multi-language FR/EN — ✅ Done (v2.0+)
- **Help system**: contextual help — ✅ Done (v2.0+)

### AP height in simulation
Add a `height_m` field to `AccessPoint` (e.g. 1.0 m default, configurable in APDialog).
The LDPL 3D model already propagates in 3D — AP height shifts the vertical distance component
`Δz` used in `propagation.py`. Relevant mainly for multi-floor analysis and for repeaters placed
at mid-height. Low priority until router/repeater model selector is done (they share the AP dialog).

### SSID + frequency band selection
Currently the SSID combo filters by network name regardless of band.
Add a **frequency/band** selector (2.4 GHz / 5 GHz / 6 GHz / All) next to the SSID combo.
The filter would apply to both the 2D heatmap and the vertical section.
Note: a single SSID can broadcast on multiple bands simultaneously (band steering);
filtering by band lets users compare coverage per radio independently.
Data already available in `MeasurementScan.frequency_mhz` (or derive band from it).

---

## Next steps

V3 complete. Continue with **Post-V3** items — router/box model selector (DB already ready),
AP placement advisor, SSID+frequency filter, or PyInstaller packaging.
