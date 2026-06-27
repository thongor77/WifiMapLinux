# WifiMapLinux — Décisions Techniques

> ADR : Architecture Decision Record.
> Format : contexte → décision → conséquences.

---

## ADR-001 — Stack UI : application desktop PySide6

**Date :** 2026-06-10
**Statut :** Décidé

**Contexte :**
Deux options envisagées : web local (FastAPI + JS, comme WifiMapper) ou application desktop native (PySide6).
Le projet cible Linux. La vue 3D et l'outil de recalage visuel nécessitent une interaction riche sur le canvas.

**Décision :** Application desktop Python + PySide6.

**Conséquences :**
- Pas de FastAPI, pas de serveur HTTP, pas de navigateur
- UI : PySide6 (Qt6) — widgets, QGraphicsView, QPainter
- Heatmap 2D : overlay sur QGraphicsScene ou QWidget + QPainter
- Vue coupe verticale : QWidget + QPainter
- Stockage : SQLite via SQLModel ou sqlite3 directement (accès local)
- Scanner Wi-Fi : subprocess iw/nmcli (inchangé)
- Packaging : PyInstaller → binaire unique Linux (inchangé)
- Cohérence avec NMLinux (qui utilise PySide6) — même écosystème

**Lien avec autres ADR :** ADR-002 (vue 3D) et ADR-003 (recalage) sont implémentés en PySide6.

---

## ADR-002 — Vue 3D : floor tabs 2D + section transversale

**Date :** 2026-06-10
**Statut :** Décidé

**Contexte :**
Trois options étudiées :
- A) Three.js voxels 3D interactifs — vrai 3D, mais suppose un navigateur web (incompatible ADR-001)
- B) Onglets par étage + section transversale 2D (coupe verticale)
- C) Animation de transition entre étages seulement

**Décision :** Option B — navigation par étage + vue en coupe verticale.

**Implémentation PySide6 :**
- `FloorTabBar` : barre d'onglets ou liste latérale — un onglet par étage
- `FloorPlanWidget` : QGraphicsView — plan 2D + overlay heatmap de l'étage actif
- `SectionView` : QWidget + QPainter — coupe XZ ou YZ configurable par l'utilisateur
  - Axe horizontal = distance en mètres sur le plan
  - Axe vertical = empilage des étages (Z = hauteur cumulée)
  - Couleur = RSSI (même palette que la heatmap 2D)

**Conséquences :**
- Pas de dépendance Three.js / WebGL / navigateur
- Heatmap 3D = deux vues 2D synchronisées (plan + coupe) — moins spectaculaire mais lisible
- `SectionView` nécessite un axe de coupe (ligne tracée par l'utilisateur sur le plan de l'étage actif)
- La grille de calcul reste 150×150 par étage → N étages → N grilles 2D indépendantes

---

## ADR-003 — Alignement XY inter-étages : assistant de recalage visuel

**Date :** 2026-06-10
**Statut :** Décidé

**Contexte :**
Les plans PNG de chaque étage ont des dimensions différentes et des origines incohérentes.
L'alignement XY est nécessaire pour que la propagation inter-étages et la vue en coupe soient cohérentes.
Options envisagées : offset saisi manuellement, ou outil de recalage visuel interactif.

**Décision :** Assistant de recalage visuel intégré à PySide6.

**Fonctionnement :**
1. L'utilisateur ouvre l'assistant depuis la configuration de l'étage N
2. L'étage de référence (inférieur, ex: RDC) est affiché à pleine opacité
3. L'étage N est superposé en semi-transparent (opacité ~50%)
4. L'utilisateur déplace l'étage N avec la souris pour aligner les points de repère
5. L'utilisateur peut zoomer dans la vue (zoom canvas, pas redimensionnement du plan) pour plus de précision
6. Validation → `Floor.offset_x_m` et `Floor.offset_y_m` sauvegardés

**Implémentation :**
- Widget dédié `FloorAlignmentWidget(QGraphicsView)`
- Plan de référence : `QGraphicsPixmapItem` à opacité 1.0
- Plan à aligner : `QGraphicsPixmapItem` à opacité 0.5, draggable
- Drag : `mousePressEvent` / `mouseMoveEvent` sur le pixmap semi-transparent
- Zoom vue : `wheelEvent` sur le QGraphicsView (scale de la scène)
- Conversion pixels → mètres via `scale_px_per_m` de l'étage de référence

**Conséquences :**
- `Floor.offset_x_m` et `Floor.offset_y_m` sont définis dès que l'alignement est effectué
- L'assistant est optionnel — si non utilisé, offset = (0, 0) et les étages sont supposés alignés
- Rotation non supportée en v1 (plans supposés orientés de la même façon)

---

## ADR-004 — Atténuation dalle inter-étages : types prédéfinis ITU-R P.1238

**Date :** 2026-06-27
**Statut :** Décidé

**Contexte (INC-05) :**
La simulation Log-Distance Path Loss 3D (V2.1) nécessite une valeur d'atténuation pour chaque dalle entre étages.
Cette valeur dépend du matériau de construction et varie significativement (bois léger vs béton armé).
Deux approches envisagées : saisie libre (valeur numérique directe) ou sélection parmi types prédéfinis.

**Décision :** 3 types de dalle prédéfinis, issus du modèle ITU-R P.1238 (référence indoor radio propagation).
L'utilisateur choisit le type par étage dans la configuration de l'étage. Pas de saisie libre en V2.

| Type | Constante | Atténuation |
|------|-----------|-------------|
| Bois / plancher léger | `FLOOR_WOOD` | 5 dB |
| Béton | `FLOOR_CONCRETE` | 12 dB |
| Béton armé | `FLOOR_REINFORCED` | 18 dB |

**Valeur par défaut :** Béton (12 dB) — matériau le plus courant dans le bâti résidentiel français.

**Conséquences :**
- `Floor` reçoit un champ `floor_material` (enum : `wood` / `concrete` / `reinforced`) stocké en SQLite
- Le modèle de propagation lit `floor_material` pour obtenir l'atténuation en dB à appliquer sur l'axe Z
- Les valeurs 5/12/18 dB sont des constantes nommées dans un module `app/services/propagation.py`
- Saisie libre de l'atténuation différée en post-V3 si le besoin est exprimé

**Référence :** ITU-R P.1238-10, Table 4 — Floor penetration loss factor (residential).

---

## ADR-005 — Seuil "zone faible" advisor : −70 dBm configurable

**Date :** 2026-06-27
**Statut :** Décidé

**Contexte (INC-06) :**
L'advisor (Post-V3) doit identifier les zones de couverture insuffisante pour recommander un placement d'AP.
Il faut un seuil RSSI en dessous duquel une zone est considérée "faible".
Question : valeur fixe ou configurable ? Et quelle valeur par défaut ?

**Décision :** Seuil par défaut à **−70 dBm**, configurable par l'utilisateur dans les préférences (champ entier, en dBm).

**Justification du seuil :**
- > −60 dBm : signal bon (streaming HD, VoIP fiable)
- −60 à −70 dBm : signal acceptable (navigation, streaming SD)
- −70 à −80 dBm : signal faible (connexion instable, décrochages fréquents)
- < −80 dBm : zone morte

−70 dBm est la frontière "acceptable / faible" retenue par la majorité des outils Wi-Fi professionnels.
C'est le seuil pertinent pour un usage résidentiel courant (streaming, visioconférence).

**Conséquences :**
- Constante `WEAK_SIGNAL_THRESHOLD_DBM = -70` dans `app/services/advisor.py`
- Préférences utilisateur : un champ `weak_signal_threshold` en dBm, stocké localement (fichier JSON ou table SQLite `settings`)
- La heatmap 2D peut optionnellement marquer les zones sous le seuil (hachures ou contour rouge) — décision d'UI différée
- Le seuil s'applique aussi bien aux mesures réelles (V1) qu'aux heatmaps simulées (V2.1)

---

## ADR-006 — Interpolation inter-étages : IDW 2D par étage + interpolation linéaire verticale

**Date :** 2026-06-27
**Statut :** Décidé

**Contexte (INC-04) :**
Question : les mesures d'un étage doivent-elles influencer la heatmap de l'étage adjacent ?
Deux options :
- A) IDW 2D indépendant par étage + interpolation linéaire dans la coupe verticale
- B) IDW 3D sur grille de voxels (une seule interpolation 3D sur tout le volume)

**Décision :** Option A — IDW 2D par étage conservé, interpolation linéaire entre milieux d'étages dans `SectionView`.

**Justification :**
- Les dalles bloquent physiquement le signal → les mesures d'un étage ne doivent pas influencer la heatmap 2D de l'étage voisin
- L'IDW 3D apporterait de la complexité sans bénéfice réel en contexte résidentiel
- L'interpolation linéaire en coupe verticale suffit pour rendre les transitions lisibles entre étages mesurés
- Décision réversible : si les tests révèlent un besoin d'IDW 3D, passer à l'option B en V2.2+

**Implémentation :**
- `FloorPlanWidget` / `idw()` : inchangé (IDW 2D par étage)
- `SectionView` : remplace les bandes solides par une image 2D interpolée
  - Z de référence de chaque étage = milieu de l'étage (z_mid = z_base + height/2)
  - `np.searchsorted` + lerp vectorisé → grille (ch × N) dBm
  - `grid_to_rgba` appliqué sur la grille complète → rendu dégradé continu
- Séparateurs d'étages et libellés maintenus visuellement par-dessus l'image interpolée

**Conséquences :**
- La coupe verticale affiche des dégradés entre étages (plus lisible que les bandes nettes)
- Un étage sans mesures est traversé par l'interpolation entre ses voisins (signal "estimé" visible)
- L'option B reste possible en V2.2+ sur décision explicite après tests utilisateur
