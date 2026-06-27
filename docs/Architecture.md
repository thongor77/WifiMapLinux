# WifiMapLinux — Architecture

> Document de référence technique. Produit en phase architecture, avant tout code.
> Dernière mise à jour : 2026-06-10

---

## 1. Définition du problème

Un propriétaire installe un ou plusieurs points d'accès Wi-Fi dans sa maison.
Il ne sait pas :
- où le signal est fort ou faible dans chaque pièce
- comment le signal traverse planchers et cloisons entre les étages
- où placer un AP supplémentaire pour éliminer les zones mortes

Les outils existants (Ekahau, NetSpot) coûtent 500–3000$/an et ciblent les réseaux d'entreprise.
WifiMapLinux résout ce problème pour un usage résidentiel, gratuitement, sous Linux.

---

## 2. Utilisateurs cibles

**Utilisateur principal — particulier autonome**
- Propriétaire ou locataire
- À l'aise avec Linux (pas nécessairement développeur)
- Veut comprendre et améliorer sa couverture Wi-Fi sans investissement matériel immédiat
- Maison de 1 à 4 étages, 1 à 6 APs

**Utilisateur secondaire — technicien réseau indépendant**
- Installe des réseaux Wi-Fi résidentiels/petites structures
- Veut un outil gratuit pour documenter une installation et justifier ses recommandations

---

## 3. Cas d'usage

### UC-01 — Audit de la couverture existante
1. L'utilisateur importe le plan de chaque étage (PNG)
2. Il calibre l'échelle (2 clics → distance réelle)
3. Il se déplace dans la maison, marque sa position et déclenche un scan Wi-Fi
4. L'outil génère une heatmap par étage à partir des mesures réelles

### UC-02 — Simulation avant déploiement
1. L'utilisateur crée une maison sans mesures
2. Il place des APs virtuels sur les plans d'étage
3. Il trace les obstacles (murs, dalles)
4. L'outil calcule la couverture simulée par modèle Log-Distance Path Loss

### UC-03 — Vue 3D de la couverture
1. À partir des données d'audit ou de simulation, l'utilisateur bascule sur la vue 3D
2. Il voit la couverture de l'ensemble du volume de la maison (étages empilés)
3. Il peut sélectionner un étage ou faire tourner la vue

### UC-04 — Conseils de placement
1. Après audit, l'outil identifie les zones de faible signal (RSSI < seuil configurable)
2. Il propose des emplacements optimaux pour un AP supplémentaire
3. Il simule l'effet du placement proposé sur la couverture globale

### UC-05 — Comparaison simulation / réalité
1. L'utilisateur a simulé une installation, puis mesuré la réalité
2. Il superpose les deux heatmaps pour identifier les écarts
3. Il calibre le modèle de propagation si besoin

---

## 4. Hors scope

- Authentification / multi-utilisateur / cloud
- Support Windows, macOS
- Mesures Bluetooth, Zigbee, 4G/5G, Thread
- Ray-tracing 3D (modèle de propagation physique)
- Interface mobile
- Gestion des VLANs / configurations réseau

---

## 5. Couches système

Décision ADR-001 : application desktop PySide6 (pas de serveur web).

```
PySide6 — Application desktop Linux
├── MainWindow
│   ├── BuildingSelector      — liste et création des maisons
│   ├── FloorTabBar           — onglets par étage (index, label)
│   ├── FloorPlanWidget       — QGraphicsView : plan 2D + overlay heatmap
│   │   ├── FloorPlanItem     — QGraphicsPixmapItem : image du plan
│   │   ├── HeatmapOverlay    — QGraphicsPixmapItem semi-transparent (RSSI coloré)
│   │   ├── APItem            — QGraphicsItem draggable : point d'accès
│   │   └── ObstacleItem      — QGraphicsLineItem : segment obstacle
│   ├── SectionView           — QWidget + QPainter : coupe verticale XZ ou YZ
│   │   └── SectionLine       — ligne de coupe tracée sur FloorPlanWidget
│   ├── MeasurePanel          — déclenchement scan + marquage position
│   ├── AdvisorPanel          — recommandations de placement AP
│   └── FloorAlignmentWidget  — QGraphicsView : recalage visuel inter-étages (ADR-003)

Services Python (appelés directement, sans HTTP)
├── propagation.py    — Log-Distance Path Loss 3D (avec dz inter-étages + atténuation dalle)
├── interpolation.py  — IDW 2D par étage (grille 150×150)
├── scanner.py        — subprocess iw/nmcli avec fallback automatique
├── advisor.py        — détection zones faibles + recommandations placement AP
└── alignment.py      — conversion offset pixels → mètres pour le recalage

Stockage
└── SQLite            — data/wifimaplinux.db (une DB globale multi-maisons)
```

---

## 6. Algorithmes envisagés

### 6.1 Propagation Wi-Fi (simulation)

Modèle Log-Distance Path Loss (identique à WifiMapper, étendu au 3D) :

```
RSSI = Ptx + Gant - PL0 - 10·n·log10(d/d0) - Σ atténuation_obstacles
```

Extension inter-étages :
- La distance `d` est calculée en 3D : `d = sqrt(dx² + dy² + dz²)`
- `dz` = différence de hauteur entre AP et point de mesure (étage × hauteur_étage + hauteur_AP)
- Les dalles inter-étages sont des obstacles horizontaux avec atténuation propre (~10–20 dB)

### 6.2 Interpolation IDW (audit terrain)

Pour la heatmap 2D par étage (identique à WifiMapper) :
```
H(x,y) = Σ(wi·vi) / Σ(wi)    avec wi = 1/d(x,y,i)^p,  p=2
```

Pour la heatmap 3D (inconnue ouverte — voir section 8) :
- Option A : IDW 2D indépendant par étage + interpolation linéaire inter-étages
- Option B : IDW 3D sur grille de voxels

### 6.3 Conseils de placement (advisor)

Heuristique v1 (simple) :
1. Seuillage : identifier toutes les cellules avec RSSI < −70 dBm
2. Clustering DBSCAN ou simple grille : regrouper les zones faibles adjacentes
3. Pour chaque cluster : calculer le barycentre
4. Simuler l'effet d'un AP au barycentre → si gain > seuil → recommander
5. Répéter jusqu'à N recommandations

Évolution possible : optimisation greedy (maximisation couverture par AP ajouté).

---

## 7. Système de coordonnées

### Espace plan (2D, par étage)
- Origine : coin supérieur gauche du plan importé
- Unité stockée : pixels
- Unité de calcul : mètres (conversion via `scale_px_per_m`)
- `x_m = x_px / scale_px_per_m`

### Espace 3D (maison complète)
- Origine : coin supérieur gauche du RDC (floor.index = 0)
- `Z = Σ hauteurs étages inférieurs + height_on_floor`
- Alignement XY via `Floor.offset_x_m / offset_y_m` définis par l'assistant de recalage (ADR-003)

---

## 8. Contraintes techniques

- **Linux uniquement** : `iw` et `nmcli` sont Linux-only
- **Scan Wi-Fi** : nécessite des droits suffisants (root ou CAP_NET_RAW selon distro)
- **Performance heatmap 3D** : grille 150×150×N (N étages) = ~112 500 voxels pour 5 étages → acceptable
- **Plans d'étage** : format PNG uniquement (v1) — SVG avec détection de murs est post-v1
- **Pas de cloud** : tout tourne en local, aucune donnée envoyée à l'extérieur
- **Un seul utilisateur simultané** : pas de gestion de concurrence SQLite

---

## 9. Inconnues ouvertes

| ID | Question | Impact | Priorité | Statut |
|----|----------|--------|----------|--------|
| INC-01 | Stack UI | Architecture entière | Haute | ✅ PySide6 — ADR-001 |
| INC-02 | Vue 3D | Complexité UI | Haute | ✅ Floor tabs + coupe verticale — ADR-002 |
| INC-03 | Alignement XY inter-étages | Modèle données + UX | Haute | ✅ Assistant recalage visuel — ADR-003 |
| INC-04 | **IDW 3D** : IDW 2D par étage + interpolation linéaire, ou IDW 3D sur voxels ? | Algorithme + perf | Moyenne | Ouvert |
| INC-05 | **Atténuation dalle** : valeurs par défaut bois, béton, brique ? | Précision modèle | Moyenne | Ouvert |
| INC-06 | **Seuil advisor** : RSSI < −70 dBm = zone faible ? Configurable ? | UX advisor | Basse | Ouvert |

> Documenter les nouvelles décisions dans `docs/Decisions-Techniques.md`.
