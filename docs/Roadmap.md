# WifiMapLinux — Roadmap

> Dernière mise à jour : 2026-06-11
> V1 complète. V1.1→V1.5 terminées et testées.

---

## Vue d'ensemble

| Version | Périmètre | État |
|---------|-----------|------|
| **Phase archi** | Architecture, modèles, décisions techniques | ✅ Terminé |
| **V1** | Import plans · Mesures Wi-Fi · Heatmap 2D · Multi-étages · Coupe verticale | ✅ Terminé |
| **V2** | Simulation · Interpolation avancée · Export | 📋 Planifié |
| **V3** | Visualisation 3D | 📋 Planifié |
| **Post-V3** | Conseils de placement AP · Simulation · Packaging PyInstaller | 💭 Différé |

---

## V1 — Application fonctionnelle

Objectif : l'utilisateur peut mesurer sa couverture Wi-Fi sur une maison multi-étages
et voir le résultat en heatmap 2D + coupe verticale.

### V1.1 — Import plans ✅

### V1.2 — Mesures Wi-Fi ✅

### V1.3 — Heatmap 2D ✅

### V1.4 — Multi-étages ✅

### V1.5 — Coupe verticale ✅

- Ligne de coupe 2 clics sur le plan (jaune pointillée)
- `SectionView` en bas du plan : bandes par étage colorées RSSI, axe distance en mètres
- Mise à jour automatique au changement de mesure ou de filtre SSID

---

## V2 — Enrichissement

### V2.1 — Simulation ✅

- Placement d'APs virtuels sur les plans d'étage (`AccessPoint` SQLite)
- Modèle Log-Distance Path Loss 3D — `app/services/propagation.py` (ITU-R P.1238, n=3.0, FAF par étage ADR-004)
- Heatmap simulée par étage (même rendu que V1.3, couche z=4 sous la heatmap mesurée z=5)
- Superposition simulation / mesures réelles : toggle "Simulation" indépendant du toggle "Heatmap"

### V2.2 — Interpolation avancée ✅

INC-04 résolu → ADR-006 : Option A (IDW 2D par étage + interpolation linéaire verticale).
- `SectionView` refondu : image 2D (ch × N) construite par lerp vectorisé entre midpoints d'étages
- Les transitions entre étages sont désormais des dégradés continus (plus de bandes nettes)
- Un étage sans mesures est traversé par l'interpolation entre ses voisins
- IDW 2D par étage inchangé (heatmap plan reste indépendante par étage)

### V2.3 — Export ✅

- Export PNG : plan + heatmap overlay annotés (Pillow) — menu Export › PNG (Ctrl+E)
  - Exporte la heatmap active (mesurée ou simulée selon les toggles)
  - Bannière : maison, étage, SSID, stats RSSI, date
- Export PDF : rapport de couverture multi-pages — menu Export › PDF (Ctrl+Shift+E)
  - Page de résumé : tableau par étage (points, RSSI min/moy/max)
  - Une page par étage : plan + heatmap mesurée + bannière
  - Généré avec Pillow (1200 px/page, 150 DPI)

---

## V3 — Visualisation 3D

Technologie à décider (INC-04 adjacente) :
- Qt3D (natif PySide6) — intégration propre mais API complexe
- vispy — librairie Python OpenGL légère, bonne pour les volumes de données
- matplotlib 3D — simple mais limité et lent pour l'interactivité

Périmètre envisagé :
- Volume voxel 3D de la maison (grilles 2D par étage empilées)
- Navigation : rotation, sélection d'étage, transparence
- Synchronisation avec la vue 2D par étage

---

## Post-V3 (différé)

- **Conseils de placement AP** : détection zones faibles, clustering, recommandation position
- **Packaging** : PyInstaller → binaire unique Linux
- **Export SVG** : import plan avec détection automatique de murs
- **Module Rust (PyO3)** : si besoin de performance sur propagation/interpolation

---

## Prochaines tâches immédiates

V2 complète. Démarrer **V3** (visualisation 3D) ou **Post-V3** (advisor zones faibles) selon priorité.
