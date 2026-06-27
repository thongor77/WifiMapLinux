# WifiMapLinux — Modèles de données

> Dernière mise à jour : 2026-06-10
> Phase architecture — aucun code produit.

---

## Vue d'ensemble

```
Building (Maison)
└── Floor (Etage) [1..N]
    ├── FloorPlan (Plan d'étage) [0..1]
    ├── AccessPoint (AP) [0..N]
    ├── Obstacle [0..N]
    └── MeasurementPoint (Point de mesure) [0..N]
            └── MeasurementScan (Scan Wi-Fi) [1..N]
```

---

## Building — Maison

Conteneur principal. Regroupe tous les étages d'une maison.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int PK | Identifiant |
| `name` | str | Nom affiché (ex: "Maison principale") |
| `address` | str? | Adresse optionnelle (non géolocalisée) |
| `created_at` | datetime | Date de création |

**Contraintes :**
- Un Building contient au moins 1 Floor.

---

## Floor — Etage

Représente un niveau physique de la maison.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int PK | Identifiant |
| `building_id` | int FK | Maison parente |
| `index` | int | Niveau : -1=cave, 0=RDC, 1=1er, 2=2e... |
| `label` | str | Libellé affiché (ex: "Rez-de-chaussée") |
| `height_m` | float | Hauteur sous plafond en mètres (ex: 2.5) |
| `floor_attenuation_db` | float | Atténuation traversée de dalle (défaut: 12 dB) |
| `offset_x_m` | float | Décalage X en mètres par rapport au RDC (alignement XY) |
| `offset_y_m` | float | Décalage Y en mètres par rapport au RDC (alignement XY) |

**Notes :**
- `height_m` sert au calcul de `dz` dans la propagation 3D
- `floor_attenuation_db` modélise la dalle entre cet étage et celui du dessous
- `offset_x_m / offset_y_m` permettent l'alignement des plans de tailles différentes (INC-03)
- L'ordre d'empilement est déterminé par `index` (croissant = du bas vers le haut)

---

## FloorPlan — Plan d'étage

Plan 2D importé pour un étage. Relation 1:1 avec Floor.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int PK | Identifiant |
| `floor_id` | int FK unique | Etage associé |
| `image_path` | str | Chemin local vers le fichier PNG |
| `width_px` | int | Largeur du plan en pixels |
| `height_px` | int | Hauteur du plan en pixels |
| `scale_px_per_m` | float? | Facteur de calibration (null = non calibré) |
| `calibration_p1_x` | int? | Premier point de calibration (x, pixels) |
| `calibration_p1_y` | int? | Premier point de calibration (y, pixels) |
| `calibration_p2_x` | int? | Deuxième point de calibration (x, pixels) |
| `calibration_p2_y` | int? | Deuxième point de calibration (y, pixels) |
| `calibration_dist_m` | float? | Distance réelle entre les deux points (mètres) |

**Note :** tant que `scale_px_per_m` est null, la simulation et l'interpolation sont désactivées.

---

## AccessPoint — Point d'accès Wi-Fi

AP réel (mesuré) ou virtuel (simulation).

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int PK | Identifiant |
| `floor_id` | int FK | Etage où est positionné l'AP |
| `x_px` | float | Position X sur le plan (pixels) |
| `y_px` | float | Position Y sur le plan (pixels) |
| `height_on_floor_m` | float | Hauteur de l'AP sur l'étage (ex: 1.5m = mural) |
| `name` | str | Nom affiché (ex: "Livebox RDC") |
| `is_virtual` | bool | True = simulation, False = AP réel connu |
| `band` | enum | `2.4GHz` / `5GHz` / `6GHz` |
| `tx_power_dbm` | float | Puissance d'émission (défaut: 20 dBm) |
| `antenna_gain_dbi` | float | Gain antenne (défaut: 2.0 dBi) |
| `path_loss_exponent` | float | Exposant de perte (défaut: 2.5) |

**Valeurs PL0 par bande (perte espace libre à 1m) :**
- 2.4 GHz : 40.0 dB
- 5 GHz : 46.7 dB
- 6 GHz : 48.0 dB

---

## Obstacle

Segment atténuateur sur le plan d'un étage (mur, vitre, cloison).
Les dalles inter-étages sont modélisées dans `Floor.floor_attenuation_db`, pas ici.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int PK | Identifiant |
| `floor_id` | int FK | Etage auquel appartient l'obstacle |
| `type` | enum | `glass` / `wall` / `concrete_light` / `concrete_heavy` |
| `x1_px`, `y1_px` | float | Premier point du segment (pixels) |
| `x2_px`, `y2_px` | float | Deuxième point du segment (pixels) |
| `attenuation_db` | float? | Atténuation override (null = valeur par défaut du type) |

**Atténuations par défaut :**

| Type | Code | dB |
|------|------|----|
| Vitre | `glass` | 2 |
| Cloison placo | `wall` | 5 |
| Béton léger | `concrete_light` | 12 |
| Béton épais | `concrete_heavy` | 20 |

---

## MeasurementPoint — Point de mesure terrain

Position géographique où l'utilisateur a effectué un scan.

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int PK | Identifiant |
| `floor_id` | int FK | Etage où le scan a été effectué |
| `x_px` | float | Position X sur le plan (pixels) |
| `y_px` | float | Position Y sur le plan (pixels) |
| `label` | str? | Libellé optionnel (ex: "Cuisine", "Couloir 1er") |
| `created_at` | datetime | Timestamp du scan |

---

## MeasurementScan — Réseau Wi-Fi détecté à un point

Un point de mesure contient N scans (un par réseau Wi-Fi détecté).

| Champ | Type | Description |
|-------|------|-------------|
| `id` | int PK | Identifiant |
| `measurement_point_id` | int FK | Point de mesure parent |
| `ssid` | str | Nom du réseau |
| `bssid` | str | Adresse MAC du point d'accès |
| `signal_dbm` | int | Signal en dBm (ex: -62) |
| `channel` | int | Canal Wi-Fi |
| `frequency_mhz` | int | Fréquence en MHz (ex: 5180) |
| `timestamp` | datetime | Horodatage exact du scan |

---

## CoverageCell — Résultat de heatmap (non persisté)

Calculé à la demande, jamais stocké en base.

| Champ | Type | Description |
|-------|------|-------------|
| `floor_id` | int | Etage concerné |
| `x_px` | float | Position X (centre de cellule) |
| `y_px` | float | Position Y (centre de cellule) |
| `signal_dbm` | float | Signal calculé (simulation) ou interpolé (audit) |
| `source` | enum | `simulation` / `interpolation` / `combined` |

Pour la vue 3D, les CoverageCell de tous les étages sont transmises au frontend sous forme de grille de voxels.

---

## Relations et cardinalités

```
Building 1 ──< Floor N
Floor    1 ──< FloorPlan (0 ou 1)
Floor    1 ──< AccessPoint N
Floor    1 ──< Obstacle N
Floor    1 ──< MeasurementPoint N
MeasurementPoint 1 ──< MeasurementScan N
```

---

## Inconnues ouvertes — modèle

| ID | Question |
|----|----------|
| INC-03 | Alignement XY inter-étages : `offset_x_m / offset_y_m` suffisent-ils, ou faut-il une rotation ? |
| INC-06 | Une DB par maison (un fichier SQLite par Building) ou une DB globale multi-maisons ? |
| — | Faut-il stocker les grilles de heatmap calculées pour accélération (cache) ? |
| — | Modèle pour les sessions de mesure (ScanSession) — utile pour grouper les points d'une même visite ? |
