# WifiMapLinux — Architecture Decisions

> ADR: Architecture Decision Record.
> Format: context → decision → consequences.

---

## ADR-001 — UI stack: PySide6 desktop application

**Date:** 2026-06-10
**Status:** Decided

**Context:**
Two options considered: local web app (FastAPI + JS, like WifiMapper) or native desktop application (PySide6).
The project targets Linux. The 3D view and the visual alignment tool require rich canvas interaction.

**Decision:** Python + PySide6 desktop application.

**Consequences:**
- No FastAPI, no HTTP server, no browser required
- UI: PySide6 (Qt6) — widgets, QGraphicsView, QPainter
- 2D heatmap: overlay on QGraphicsScene or QWidget + QPainter
- Vertical section view: QWidget + QPainter
- Storage: SQLite via SQLModel (local access)
- Wi-Fi scanner: subprocess iw/nmcli (unchanged)
- Packaging: PyInstaller → single Linux binary (future)
- Consistent with NMLinux (also uses PySide6) — same ecosystem

**Related ADRs:** ADR-002 (3D view) and ADR-003 (alignment) are implemented in PySide6.

---

## ADR-002 — 3D view: floor tabs + vertical cross-section

**Date:** 2026-06-10
**Status:** Decided

**Context:**
Three options studied:
- A) Three.js interactive 3D voxels — true 3D, but requires a web browser (incompatible with ADR-001)
- B) Per-floor tabs + 2D vertical cross-section
- C) Floor transition animation only

**Decision:** Option B — per-floor navigation + vertical section view.

**PySide6 implementation:**
- `FloorTabBar`: tab bar — one tab per floor
- `FloorPlanWidget`: QGraphicsView — 2D floor plan + heatmap overlay for the active floor
- `SectionView`: QWidget + QPainter — XZ or YZ cross-section configurable by the user
  - Horizontal axis = distance in metres along the section line
  - Vertical axis = stacked floors (Z = cumulative height)
  - Colour = RSSI (same palette as the 2D heatmap)

**Consequences:**
- No Three.js / WebGL / browser dependency
- 3D heatmap = two synchronised 2D views (plan + section) — less spectacular but readable
- `SectionView` requires a cut axis (line drawn by the user on the active floor plan)
- Computation grid remains 150×150 per floor → N floors → N independent 2D grids

---

## ADR-003 — XY inter-floor alignment: visual alignment assistant

**Date:** 2026-06-10
**Status:** Decided

**Context:**
Floor plan PNGs have different dimensions and inconsistent origins.
XY alignment is required for inter-floor propagation and the section view to be coherent.
Options considered: manual offset entry, or interactive visual alignment tool.

**Decision:** Visual alignment assistant integrated into PySide6.

**Workflow:**
1. User opens the assistant from floor N's configuration
2. The reference floor (lower, e.g. ground floor) is displayed at full opacity
3. Floor N is overlaid semi-transparently (opacity ~50%)
4. User drags floor N with the mouse to align reference landmarks
5. User can zoom into the view (canvas zoom, not plan resize) for precision
6. Confirm → `Floor.offset_x_m` and `Floor.offset_y_m` saved

**Implementation:**
- Dedicated widget `FloorAlignmentWidget(QGraphicsView)`
- Reference plan: `QGraphicsPixmapItem` at opacity 1.0
- Plan to align: `QGraphicsPixmapItem` at opacity 0.5, draggable
- Drag: `mousePressEvent` / `mouseMoveEvent` on the semi-transparent pixmap
- View zoom: `wheelEvent` on the QGraphicsView (scene scale)
- Pixel → metre conversion via `scale_px_per_m` of the reference floor

**Consequences:**
- `Floor.offset_x_m` and `Floor.offset_y_m` are set once alignment is performed
- The assistant is optional — if unused, offset = (0, 0) and floors are assumed aligned
- Rotation not supported in v1 (plans assumed to share the same orientation)

---

## ADR-004 — Inter-floor slab attenuation: ITU-R P.1238 presets

**Date:** 2026-06-27
**Status:** Decided

**Context (INC-05):**
The 3D Log-Distance Path Loss simulation (V2.1) requires an attenuation value for each inter-floor slab.
This value depends on the building material and varies significantly (light wood vs. reinforced concrete).
Two approaches considered: free numeric input, or selection from predefined types.

**Decision:** 3 predefined slab types from the ITU-R P.1238 model (indoor radio propagation reference).
The user selects the type per floor in the floor configuration dialog. No free input in V2.

| Type | Constant | Attenuation |
|------|----------|-------------|
| Wood / light floor | `FLOOR_WOOD` | 5 dB |
| Concrete | `FLOOR_CONCRETE` | 12 dB |
| Reinforced concrete | `FLOOR_REINFORCED` | 18 dB |

**Default:** Concrete (12 dB) — most common material in residential buildings.

**Consequences:**
- `Floor` receives a `floor_attenuation_db` field (float) stored in SQLite
- The propagation model reads `floor_attenuation_db` to obtain the Z-axis attenuation in dB
- The 5/12/18 dB values are named constants in `app/services/propagation.py`
- Free attenuation input deferred to post-V3 if the need arises

**Reference:** ITU-R P.1238-10, Table 4 — Floor penetration loss factor (residential).

---

## ADR-005 — Weak zone threshold: −70 dBm, configurable

**Date:** 2026-06-27
**Status:** Decided

**Context (INC-06):**
The advisor (Post-V3) must identify insufficient coverage zones to recommend AP placement.
A RSSI threshold is needed below which a zone is considered "weak".
Question: fixed value or configurable? And what default?

**Decision:** Default threshold at **−70 dBm**, configurable by the user in preferences (integer field, in dBm).

**Threshold rationale:**
- > −60 dBm: good signal (HD streaming, reliable VoIP)
- −60 to −70 dBm: acceptable signal (browsing, SD streaming)
- −70 to −80 dBm: weak signal (unstable connection, frequent drops)
- < −80 dBm: dead zone

−70 dBm is the "acceptable / weak" boundary used by the majority of professional Wi-Fi tools.
It is the relevant threshold for typical residential use (streaming, video calls).

**Consequences:**
- Constant `WEAK_SIGNAL_THRESHOLD_DBM = -70` in `app/services/advisor.py`
- User preferences: a `weak_signal_threshold` field in dBm, stored locally (JSON file or SQLite `settings` table)
- The 2D heatmap can optionally mark zones below the threshold (hatching or red outline) — UI decision deferred
- The threshold applies to both real measurements (V1) and simulated heatmaps (V2.1)

---

## ADR-006 — Inter-floor interpolation: per-floor IDW + vertical linear interpolation

**Date:** 2026-06-27
**Status:** Decided

**Context (INC-04):**
Question: should measurements from one floor influence the heatmap of the adjacent floor?
Two options:
- A) Independent 2D IDW per floor + linear interpolation in the vertical section view
- B) 3D IDW on a voxel grid (single 3D interpolation over the entire volume)

**Decision:** Option A — per-floor 2D IDW retained, linear interpolation between floor midpoints in `SectionView`.

**Rationale:**
- Slabs physically block the signal → measurements from one floor should not influence the adjacent floor's 2D heatmap
- 3D IDW would add complexity without real benefit in a residential context
- Linear interpolation in the vertical section is sufficient to make transitions between measured floors readable
- Reversible decision: if testing reveals a need for 3D IDW, switch to option B in V2.2+

**Implementation:**
- `FloorPlanWidget` / `idw()`: unchanged (per-floor 2D IDW)
- `SectionView`: replaces solid bands with an interpolated 2D image
  - Reference Z for each floor = floor midpoint (z_mid = z_base + height/2)
  - `np.searchsorted` + vectorised lerp → (ch × N) dBm grid
  - `grid_to_rgba` applied to the full grid → continuous gradient rendering
- Floor separators and labels drawn on top of the interpolated image

**Consequences:**
- The vertical section displays gradients between floors (more readable than hard bands)
- A floor without measurements is traversed by interpolation between its neighbours (estimated signal visible)
- Option B remains possible in V2.2+ on explicit decision after user testing
