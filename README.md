# WifiMapLinux

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![PySide6](https://img.shields.io/badge/UI-PySide6%20%28Qt6%29-41cd52.svg)](https://doc.qt.io/qtforpython/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Donate](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?business=JFQGY7NU3ANCN&no_recurring=0&item_name=Every+donation%2C+no+matter+how+small%2C+helps+me+keep+this+project+alive.+Thank+you%21%0A&currency_code=EUR)
[![Bitcoin](https://img.shields.io/badge/Donate-Bitcoin-orange.svg)](#support-the-project)

Outil de cartographie Wi-Fi résidentiel pour Linux.  
Mesure la couverture réelle dans une maison multi-étages, génère des heatmaps, simule le placement d'APs et exporte des rapports de couverture.

---

## Fonctionnalités

- **Audit terrain** — scan Wi-Fi (`iw`/`nmcli`) + marquage de position sur le plan → heatmap 2D par étage
- **Simulation AP** — placement virtuel de points d'accès + modèle Log-Distance Path Loss 3D (ITU-R P.1238)
- **Vue multi-étages** — navigation par onglets, recalage visuel inter-étages, coupe verticale interpolée
- **Overlay comparaison** — superposition heatmap mesurée / heatmap simulée
- **Export** — PNG annoté (plan + heatmap) et rapport PDF multi-pages

## Cible

Usage résidentiel — propriétaire ou locataire souhaitant optimiser son réseau Wi-Fi maison,
sans budget ni formation pour les outils professionnels (Ekahau, NetSpot).

## Statut

**V2 complète** — application fonctionnelle, simulation et export disponibles.  
Voir [`docs/Roadmap.md`](docs/Roadmap.md) pour le détail des versions et les prochaines étapes.

## Stack

| Couche | Techno |
|--------|--------|
| UI | Python 3.11+, PySide6 (Qt6) |
| Canvas plan + heatmap | QGraphicsView, QPainter |
| Vue coupe verticale | QWidget + QPainter |
| Propagation radio | Log-Distance Path Loss 3D (NumPy) |
| Interpolation IDW | NumPy |
| Stockage | SQLite local (SQLModel) |
| Wi-Fi scan | `iw`, `nmcli` (Linux) |
| Export | Pillow |

> Décisions architecturales dans [`docs/Decisions-Techniques.md`](docs/Decisions-Techniques.md).

## Installation

```bash
git clone https://github.com/thongor77/WifiMapLinux.git
cd WifiMapLinux
python -m venv .venv --system-site-packages
.venv/bin/pip install sqlmodel numpy pillow
.venv/bin/python main.py
```

**Prérequis système :**
- Linux (Arch, Debian, Ubuntu)
- Python 3.11+
- PySide6 disponible (système ou venv)
- `iw` ou `nmcli` pour le scan Wi-Fi

## Utilisation rapide

1. **Créer une maison** — panneau gauche → "+ Nouvelle maison" puis "+ Nouvel étage"
2. **Importer un plan** — "Importer plan PNG" → calibrer l'échelle (2 clics + distance réelle)
3. **Mesurer** — "Mesurer Wi-Fi" → cliquer sa position sur le plan
4. **Visualiser** — activer "Heatmap" dans la barre du bas
5. **Simuler** — "Placer AP virtuel" → activer "Simulation"
6. **Exporter** — menu Export → PNG ou PDF

## Structure source

```
app/
├── models/          — SQLModel : Building, Floor, FloorPlan, MeasurementPoint, AccessPoint
├── services/        — IDW, propagation LDPL, scanner Wi-Fi, export Pillow
└── ui/
    ├── main_window.py
    ├── floor_plan_widget.py   — QGraphicsView : plan + heatmaps + marqueurs
    ├── section_view.py        — coupe verticale interpolée
    ├── heatmap_controls.py    — barre de contrôles (heatmap, simulation, opacité, coupe)
    ├── building_panel.py      — arbre maisons/étages + actions
    ├── floor_tab_bar.py       — navigation onglets étages
    └── dialogs/               — FloorDialog, ScanDialog, AlignmentDialog, APDialog
```

## Support the project

Si ce projet vous est utile, vous pouvez soutenir son développement :

- **PayPal** — [Donate via PayPal](https://www.paypal.com/donate/?business=JFQGY7NU3ANCN&no_recurring=0&item_name=Every+donation%2C+no+matter+how+small%2C+helps+me+keep+this+project+alive.+Thank+you%21%0A&currency_code=EUR)
- **Bitcoin** — `bc1qspe0tky7552qas72wgn8w9dswr0dxlv24w39t6ztjqk3nz6kc5tqv753a4`

## Différences avec WifiMapper

WifiMapper (projet frère) cible les PME avec un outil web 2D mono-étage.  
WifiMapLinux cible le résidentiel, ajoute le multi-étages, la simulation 3D et les rapports de couverture.  
Les deux projets sont indépendants et ne partagent pas de code.

## Licence

MIT
