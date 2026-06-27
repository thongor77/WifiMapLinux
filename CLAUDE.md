# WifiMapLinux — Claude Context

## Project overview

Residential Wi-Fi mapping tool for Linux.
Target: homeowner or tenant wanting to optimise their Wi-Fi network in a multi-floor house.

Different from WifiMapper (enterprise sibling): residential, multi-floor, 3D heatmap, placement advice.

## Current phase

**V2 complete** — floor plan import, Wi-Fi scanning, 2D heatmap, multi-floor navigation,
vertical cross-section, AP simulation (LDPL 3D), and PNG/PDF export all implemented.

Reference documents: `docs/Architecture.md`, `docs/Data-Models.md`, `docs/Roadmap.md`.

## Running the app

```bash
cd ~/claude-projects/WifiMapLinux
.venv/bin/python main.py
```

The venv is in `.venv/` (created with `--system-site-packages` to inherit system PySide6).
SQLModel is installed in the venv: `wifimaplinux.db` is created automatically in `data/` on first launch.

## Source structure

```
app/
├── models/
│   ├── database.py        # init_db(), get_session(), DATA_DIR
│   ├── building.py        # Building (SQLModel)
│   ├── floor.py           # Floor, FloorPlan (SQLModel)
│   ├── measurement.py     # MeasurementPoint, MeasurementScan (SQLModel)
│   └── access_point.py    # AccessPoint (SQLModel)
├── services/
│   ├── interpolation.py   # IDW 2D, grid_to_rgba
│   ├── propagation.py     # LDPL 3D simulation (ITU-R P.1238)
│   ├── scanner.py         # Wi-Fi scan via iw/nmcli
│   └── export.py          # PNG/PDF export (Pillow)
└── ui/
    ├── main_window.py         # MainWindow — layout + signal connections
    ├── building_panel.py      # Left panel: house/floor tree + action buttons
    ├── floor_plan_widget.py   # QGraphicsView: floor plan + heatmaps + markers
    ├── floor_tab_bar.py       # Per-floor tab navigation
    ├── heatmap_controls.py    # Bottom bar: heatmap/simulation toggles, SSID, opacity, section
    ├── section_view.py        # Vertical cross-section (interpolated, V2.2)
    └── dialogs/
        ├── building_dialog.py
        ├── floor_dialog.py       # includes slab material selector (ADR-004)
        ├── scan_dialog.py
        ├── alignment_dialog.py   # Inter-floor visual alignment (ADR-003)
        └── ap_dialog.py          # Virtual AP placement dialog
```

## Stack (decided — ADR-001/002/003)

- UI: Python 3.11+, PySide6 (Qt6) — Linux desktop application
- Floor plan canvas + 2D heatmap: QGraphicsView / QPainter
- Vertical section view: QWidget + QPainter (floor tabs + cross-section)
- Inter-floor alignment: FloorAlignmentWidget (QGraphicsView semi-transparent overlay)
- Services: Python, NumPy (LDPL 3D propagation, IDW, advisor)
- Export: Pillow (PNG + multi-page PDF)
- Storage: SQLite local (`data/wifimaplinux.db`)
- Wi-Fi scan: subprocess `iw` + `nmcli` fallback
- Packaging: PyInstaller (future v1.0 goal)

## Conventions

- Code and identifiers: English
- Documentation and commits: English
- Commit messages: imperative present tense, one intent per commit
- No secrets in git-tracked files

## Key concepts

- **Building**: the house — container for all floors
- **Floor**: one storey with its plan, height, and slab attenuation
- **MeasurementPoint**: position on the plan + recorded Wi-Fi scans
- **AccessPoint**: virtual AP (simulation)
- **LDPL 3D**: Log-Distance Path Loss extended to 3D with inter-floor slab attenuation (ITU-R P.1238)
- **Simulated heatmap**: z=4 layer, below measured heatmap z=5 — both toggleable independently

## Technical reference

WifiMapper (`~/claude-projects/WifiMapper/`) is the reference for:
- Propagation algorithms (Log-Distance Path Loss)
- IDW interpolation
- Wi-Fi scanner (iw/nmcli)

Do not copy the code — use it as design inspiration only.

## Links

- Project: `~/claude-projects/WifiMapLinux/`
- GitHub: https://github.com/thongor77/WifiMapLinux (private)
- Claude memory: `~/.claude/projects/-home-luust-claude-projects-WifiMapLinux/memory/`
