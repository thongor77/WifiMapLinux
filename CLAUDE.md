# WifiMapLinux — Contexte Claude

## Nature du projet

Outil de cartographie Wi-Fi résidentiel Linux.
Cible : propriétaire/locataire voulant optimiser son réseau Wi-Fi maison, multi-étages.

Différent de WifiMapper (frère entreprise) : résidentiel, multi-étages, heatmap 3D, conseils placement.

## Phase actuelle

**V1.1 en cours** — structure projet, modèles SQLite, MainWindow, import plan + calibration.

Documents de référence : `docs/Architecture.md`, `docs/Modeles-Donnees.md`, `docs/Roadmap.md`.

## Lancement

```bash
cd ~/claude-projects/WifiMapLinux
.venv/bin/python main.py
```

Le venv est dans `.venv/` (créé avec `--system-site-packages` pour hériter de PySide6 système).
SQLModel installé dans le venv : `wifimaplinux.db` créé automatiquement dans `data/` au premier lancement.

## Structure source

```
app/
├── models/
│   ├── database.py      # init_db(), get_session(), DATA_DIR
│   ├── building.py      # Building (SQLModel)
│   └── floor.py         # Floor, FloorPlan (SQLModel)
└── ui/
    ├── main_window.py   # MainWindow — layout + connexions signaux
    ├── building_panel.py # Panneau gauche : arbre maisons/étages + boutons
    ├── floor_plan_widget.py # QGraphicsView : plan PNG + calibration
    └── dialogs/
        ├── building_dialog.py
        └── floor_dialog.py
```

## Stack (décidée — ADR-001/002/003)

- UI : Python 3.11+, PySide6 (Qt6) — application desktop Linux
- Canvas plan + heatmap 2D : QGraphicsView / QPainter
- Vue coupe verticale 2D : QWidget + QPainter (floor tabs + section transversale)
- Recalage inter-étages : FloorAlignmentWidget (QGraphicsView overlay semi-transparent)
- Services : Python, NumPy (propagation Log-Distance 3D, IDW, advisor)
- Stockage : SQLite local (`data/wifimaplinux.db`)
- Wi-Fi scan : subprocess `iw` + `nmcli` fallback
- Packaging : PyInstaller (objectif v1.0)

## Conventions

- Code et identifiants : anglais
- Documentation et commits : français
- Messages de commit : présent impératif, une intention par commit
- Aucun secret dans les fichiers trackés par git

## Concepts clés

- **Building** : la maison — contenant de tous les étages
- **Floor** : un étage avec son plan, sa hauteur, ses obstacles
- **MeasurementPoint** : position sur le plan + scans Wi-Fi mesurés
- **AccessPoint** : AP virtuel (simulation) ou réel (audit)
- **heatmap 3D** : visualisation de la couverture sur le volume entier de la maison

## Référence technique

WifiMapper (`~/claude-projects/WifiMapper/`) est la référence pour :
- Les algorithmes de propagation (Log-Distance Path Loss)
- L'interpolation IDW
- Le scanner Wi-Fi iw/nmcli

Ne pas copier le code — s'en inspirer pour la conception.

## Liens

- Projet : `~/claude-projects/WifiMapLinux/`
- Note Obsidian : `~/Obsidian/MyVault/Projets/WifiMapLinux.md`
- Mémoire Claude : `~/.claude/projects/-home-luust-claude-projects-WifiMapLinux/memory/`
