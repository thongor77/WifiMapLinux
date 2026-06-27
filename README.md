# WifiMapLinux

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20%28Qt6%29-41cd52.svg)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?business=JFQGY7NU3ANCN&no_recurring=0&item_name=Every+donation%2C+no+matter+how+small%2C+helps+me+keep+this+project+alive.+Thank+you%21%0A&currency_code=EUR)
[![Bitcoin](https://img.shields.io/badge/Donate-Bitcoin-orange.svg)](#support-the-project)

Residential Wi-Fi mapping tool for Linux.  
Measure real-world coverage across a multi-floor house, generate heatmaps, simulate AP placement, and export coverage reports.

---

## Features

- **Field audit** — Wi-Fi scan (`iw`/`nmcli`) + position marking on the floor plan → 2D per-floor heatmap
- **AP simulation** — virtual access point placement + Log-Distance Path Loss 3D model (ITU-R P.1238)
- **Multi-floor navigation** — per-floor tabs, visual inter-floor alignment, interpolated vertical cross-section
- **Overlay comparison** — measured heatmap vs. simulated heatmap side by side
- **Export** — annotated PNG (plan + heatmap) and multi-page PDF coverage report

## Target audience

Residential use — homeowner or tenant wanting to optimise their home Wi-Fi network,
without the budget or training required for professional tools (Ekahau, NetSpot).

## Status

**V2 complete** — fully functional application, simulation and export available.  
See [`docs/Roadmap.md`](docs/Roadmap.md) for the version history and next steps.

## Stack

| Layer | Technology |
|-------|-----------|
| UI | Python 3.11+, PySide6 (Qt6) |
| Floor plan canvas + heatmap | QGraphicsView, QPainter |
| Vertical cross-section view | QWidget + QPainter |
| Radio propagation | Log-Distance Path Loss 3D (NumPy) |
| IDW interpolation | NumPy |
| Storage | SQLite local (SQLModel) |
| Wi-Fi scan | `iw`, `nmcli` (Linux) |
| Export | Pillow |

> Architecture decisions: [`docs/Architecture-Decisions.md`](docs/Architecture-Decisions.md)

## Installation

```bash
git clone https://github.com/thongor77/WifiMapLinux.git
cd WifiMapLinux
python -m venv .venv --system-site-packages
.venv/bin/pip install sqlmodel numpy pillow
.venv/bin/python main.py
```

**System requirements:**
- Linux (Arch, Debian, Ubuntu)
- Python 3.11+
- PySide6 available (system or venv)
- `iw` or `nmcli` for Wi-Fi scanning

## Quick start

1. **Create a house** — left panel → "+ New house" then "+ New floor"
2. **Import a plan** — "Import PNG floor plan" → calibrate the scale (2 clicks + real-world distance)
3. **Measure** — "Measure Wi-Fi" → click your position on the floor plan
4. **Visualise** — enable "Heatmap" in the bottom bar
5. **Simulate** — "Place virtual AP" → enable "Simulation"
6. **Export** — Export menu → PNG or PDF

## Source structure

```
app/
├── models/          — SQLModel: Building, Floor, FloorPlan, MeasurementPoint, AccessPoint
├── services/        — IDW, LDPL propagation, Wi-Fi scanner, Pillow export
└── ui/
    ├── main_window.py
    ├── floor_plan_widget.py   — QGraphicsView: floor plan + heatmaps + markers
    ├── section_view.py        — interpolated vertical cross-section
    ├── heatmap_controls.py    — control bar (heatmap, simulation, opacity, section)
    ├── building_panel.py      — house/floor tree + action buttons
    ├── floor_tab_bar.py       — per-floor tab navigation
    └── dialogs/               — FloorDialog, ScanDialog, AlignmentDialog, APDialog
```

## Support the project

If this project is useful to you, you can support its development:

- **PayPal** — [Donate via PayPal](https://www.paypal.com/donate/?business=JFQGY7NU3ANCN&no_recurring=0&item_name=Every+donation%2C+no+matter+how+small%2C+helps+me+keep+this+project+alive.+Thank+you%21%0A&currency_code=EUR)
- **Bitcoin** — `bc1qspe0tky7552qas72wgn8w9dswr0dxlv24w39t6ztjqk3nz6kc5tqv753a4`

## Differences from WifiMapper

WifiMapper (sibling project) targets small businesses with a 2D single-floor web tool.  
WifiMapLinux targets residential use, adds multi-floor support, 3D simulation, and coverage reports.  
Both projects are independent and share no code.

## License

MIT
