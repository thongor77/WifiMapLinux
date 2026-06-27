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
| **V3** | 3D visualisation | 📋 Planned |
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

## V3 — 3D visualisation

Technology to be decided:
- Qt3D (native PySide6) — clean integration but complex API
- vispy — lightweight Python OpenGL library, good for volume data
- matplotlib 3D — simple but limited and slow for interactivity

Planned scope:
- 3D voxel volume of the house (2D grids per floor stacked)
- Navigation: rotation, floor selection, transparency
- Synchronisation with the per-floor 2D view

---

## Post-V3 (deferred)

- **AP placement advisor**: weak zone detection, clustering, position recommendation (threshold from ADR-005)
- **Packaging**: PyInstaller → single Linux binary
- **SVG export**: floor plan import with automatic wall detection
- **Rust module (PyO3)**: if performance is needed for propagation/interpolation

---

## Next steps

V2 complete. Start **V3** (3D visualisation) or **Post-V3** (weak zone advisor) depending on priority.
