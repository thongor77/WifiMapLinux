# WifiMapLinux — Architecture

> Technical reference document. Written during the architecture phase, before any code.
> Last updated: 2026-06-10

---

## 1. Problem definition

A homeowner installs one or more Wi-Fi access points in their house.
They don't know:
- where the signal is strong or weak in each room
- how the signal travels through floors and walls between storeys
- where to place an additional AP to eliminate dead zones

Existing tools (Ekahau, NetSpot) cost $500–$3,000/year and target enterprise networks.
WifiMapLinux solves this problem for residential use, for free, on Linux.

---

## 2. Target users

**Primary user — autonomous homeowner**
- Homeowner or tenant
- Comfortable with Linux (not necessarily a developer)
- Wants to understand and improve their Wi-Fi coverage without immediate hardware investment
- House with 1–4 floors, 1–6 APs

**Secondary user — independent network technician**
- Installs Wi-Fi networks in residential/small-structure settings
- Wants a free tool to document an installation and justify recommendations

---

## 3. Use cases

### UC-01 — Existing coverage audit
1. User imports each floor plan (PNG)
2. Calibrates the scale (2 clicks → real-world distance)
3. Walks through the house, marks their position and triggers a Wi-Fi scan
4. Tool generates a per-floor heatmap from real measurements

### UC-02 — Pre-deployment simulation
1. User creates a house without measurements
2. Places virtual APs on the floor plans
3. Draws obstacles (walls, slabs)
4. Tool computes simulated coverage using the Log-Distance Path Loss model

### UC-03 — 3D coverage view
1. From audit or simulation data, user switches to the 3D view
2. Sees coverage over the full house volume (stacked floors)
3. Can select a floor or rotate the view

### UC-04 — Placement advisor
1. After an audit, the tool identifies weak-signal zones (RSSI < configurable threshold)
2. Proposes optimal positions for an additional AP
3. Simulates the effect of the proposed placement on overall coverage

### UC-05 — Simulation vs. reality comparison
1. User has simulated an installation, then measured the real result
2. Overlays both heatmaps to identify discrepancies
3. Calibrates the propagation model if needed

---

## 4. Out of scope

- Authentication / multi-user / cloud
- Windows, macOS support
- Bluetooth, Zigbee, 4G/5G, Thread measurements
- 3D ray-tracing (physical propagation model)
- Mobile interface
- VLAN management / network configuration

---

## 5. System layers

Decision ADR-001: PySide6 desktop application (no web server).

```
PySide6 — Linux desktop application
├── MainWindow
│   ├── BuildingSelector      — list and create houses
│   ├── FloorTabBar           — per-floor tabs (index, label)
│   ├── FloorPlanWidget       — QGraphicsView: 2D plan + heatmap overlay
│   │   ├── FloorPlanItem     — QGraphicsPixmapItem: floor plan image
│   │   ├── HeatmapOverlay    — semi-transparent QGraphicsPixmapItem (RSSI colours)
│   │   ├── APItem            — draggable QGraphicsItem: access point
│   │   └── ObstacleItem      — QGraphicsLineItem: obstacle segment
│   ├── SectionView           — QWidget + QPainter: vertical cross-section (XZ or YZ)
│   │   └── SectionLine       — cut line drawn on FloorPlanWidget
│   ├── MeasurePanel          — trigger scan + mark position
│   ├── AdvisorPanel          — AP placement recommendations
│   └── FloorAlignmentWidget  — QGraphicsView: visual inter-floor alignment (ADR-003)

Python services (called directly, no HTTP)
├── propagation.py    — Log-Distance Path Loss 3D (with inter-floor dz + slab attenuation)
├── interpolation.py  — IDW 2D per floor (150×150 grid)
├── scanner.py        — subprocess iw/nmcli with automatic fallback
├── advisor.py        — weak zone detection + AP placement recommendations
└── alignment.py      — pixel offset → metres conversion for floor alignment

Storage
└── SQLite            — data/wifimaplinux.db (single global multi-house database)
```

---

## 6. Algorithms

### 6.1 Wi-Fi propagation (simulation)

Log-Distance Path Loss model (same as WifiMapper, extended to 3D):

```
RSSI = Ptx + Gant - PL0 - 10·n·log10(d/d0) - Σ obstacle_attenuation
```

Inter-floor extension:
- Distance `d` is computed in 3D: `d = sqrt(dx² + dy² + dz²)`
- `dz` = height difference between AP and measurement point (floor index × floor height + AP height)
- Inter-floor slabs are horizontal obstacles with their own attenuation (~10–20 dB)

### 6.2 IDW interpolation (field audit)

For the 2D per-floor heatmap (same as WifiMapper):
```
H(x,y) = Σ(wi·vi) / Σ(wi)    with wi = 1/d(x,y,i)^p,  p=2
```

For the 3D heatmap (resolved — see ADR-006):
- Option A chosen: independent 2D IDW per floor + linear interpolation in the vertical section view

### 6.3 Placement advisor

Heuristic v1 (simple):
1. Thresholding: identify all cells with RSSI < −70 dBm
2. DBSCAN clustering or simple grid: group adjacent weak zones
3. For each cluster: compute the centroid
4. Simulate an AP at the centroid → if gain > threshold → recommend
5. Repeat up to N recommendations

Possible evolution: greedy optimisation (maximise coverage per added AP).

---

## 7. Coordinate system

### Floor space (2D, per floor)
- Origin: top-left corner of the imported floor plan
- Stored unit: pixels
- Calculation unit: metres (conversion via `scale_px_per_m`)
- `x_m = x_px / scale_px_per_m`

### 3D space (full house)
- Origin: top-left corner of the ground floor (floor.index = 0)
- `Z = Σ heights of lower floors + height_on_floor`
- XY alignment via `Floor.offset_x_m / offset_y_m` set by the alignment assistant (ADR-003)

---

## 8. Technical constraints

- **Linux only**: `iw` and `nmcli` are Linux-only tools
- **Wi-Fi scan**: requires sufficient privileges (root or CAP_NET_RAW depending on distro)
- **3D heatmap performance**: 150×150×N grid (N floors) = ~112,500 voxels for 5 floors → acceptable
- **Floor plans**: PNG format only (v1) — SVG with wall detection is post-v1
- **No cloud**: everything runs locally, no data sent externally
- **Single concurrent user**: no SQLite concurrency management needed

---

## 9. Architecture decisions

All decisions are documented in `docs/Architecture-Decisions.md` (ADR-001 to ADR-006).

| ID | Decision | Status |
|----|----------|--------|
| ADR-001 | PySide6 desktop app (no web server) | ✅ |
| ADR-002 | Floor tabs + vertical section (no 3D engine) | ✅ |
| ADR-003 | Visual inter-floor alignment assistant | ✅ |
| ADR-004 | Slab attenuation: 3 ITU-R P.1238 presets | ✅ |
| ADR-005 | Weak zone threshold: −70 dBm, configurable | ✅ |
| ADR-006 | IDW 2D per floor + linear vertical interpolation | ✅ |
