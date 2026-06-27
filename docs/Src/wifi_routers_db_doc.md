# Documentation — Base de données WiFi Routers/Box

**Version** : 1.0.0 | **Date** : 2026-06-27 | **Périmètre** : Europe (ETSI)

---

## Pourquoi pas uniquement la puissance dBm ?

En Europe, **tous les routeurs sont plafonnés aux mêmes valeurs réglementaires ETSI** :

| Bande | Puissance max | Équivalent mW |
|-------|--------------|---------------|
| 2.4 GHz | 20 dBm | 100 mW |
| 5 GHz | 23 dBm | 200 mW |
| 6 GHz | 23 dBm | 200 mW |

La puissance brute n'est donc **pas discriminante** entre les modèles. Ce qui différencie réellement la portée et la qualité du signal, c'est la combinaison de :

- **Gain antenne (dBi)** → amplifie passivement le signal (PIRE effective)
- **Standard WiFi** → détermine l'efficacité spectrale
- **Configuration MIMO** → nombre de flux simultanés
- **Beamforming** → concentration du signal vers l'appareil

---

## Champ `effective_pire_dbm` — comment il est calculé

```
PIRE (dBm) = Tx Power (dBm) + Gain Antenne (dBi)
```

**Exemples :**
- ASUS RT-AX86U @ 5 GHz : 23 dBm + 5 dBi = **28 dBm** (≈ 630 mW PIRE)
- Bbox Must @ 5 GHz : 23 dBm + 2.5 dBi = **25.5 dBm** (≈ 355 mW PIRE)
- RED Box @ 5 GHz : 20 dBm + 2.5 dBi = **22.5 dBm** (≈ 178 mW PIRE)

> ⚠️ La PIRE peut dépasser le plafond de puissance brute ETSI car le gain dBi est passif.
> La limite réglementaire s'applique à la PIRE totale (variable selon pays et canal).

---

## Schéma de données complet

```json
{
  "id": "slug unique",
  "brand": "string",
  "model": "string",
  "category": "router | isp_box | mesh_system | mesh_node",
  "isp": "string | null",
  "release_year": "integer",

  "wifi_standard": "WiFi 4 | WiFi 5 | WiFi 6 | WiFi 6E | WiFi 7",
  "wifi_ieee": "802.11n | 802.11ac | 802.11ax | 802.11be",

  "bands": {
    "count": "integer",
    "list": ["2.4GHz", "5GHz", "6GHz"]
  },

  "tx_power": {
    "regulatory": "ETSI | FCC",
    "band_2_4ghz_dbm": "integer",
    "band_5ghz_dbm": "integer",
    "band_6ghz_dbm": "integer | null",
    "confidence": "verified | estimated | unavailable"
  },

  "antennas": {
    "external_count": "integer",
    "internal_count": "integer",
    "gain_dbi_typical": "float | null",
    "gain_confidence": "verified | estimated | unavailable",
    "beamforming": "boolean",
    "mu_mimo": "boolean",
    "mimo_config": "string — ex: 4x4:4"
  },

  "effective_pire_dbm": {
    "band_2_4ghz": "float | null",
    "band_5ghz": "float | null",
    "band_6ghz": "float | null"
  },

  "coverage": {
    "area_m2": "integer | null",
    "area_confidence": "verified | estimated"
  },

  "max_devices": "integer | null",

  "ethernet": {
    "wan_ports": "integer",
    "lan_ports": "integer",
    "max_speed_gbps": "float"
  },

  "mesh_capable": "boolean",
  "mesh_protocol": "string | null",

  "data_sources": ["string"]
}
```

---

## Niveaux de confiance (`confidence`)

| Valeur | Signification |
|--------|--------------|
| `verified` | Donnée issue d'un filing FCC, datasheet officiel ou deviwiki |
| `estimated` | Valeur typique de la gamme déduite du standard et de la catégorie |
| `unavailable` | Donnée non publiée et introuvable dans les sources ouvertes |

---

## Limites connues et avertissements

### Box FAI (isp_box)
Les opérateurs français **ne publient jamais** le gain d'antenne ni la configuration MIMO précise de leurs box. Les valeurs `gain_dbi_typical` et `mimo_config` sont des estimations basées sur :
- La catégorie de produit (entrée/milieu/haut de gamme)
- Les mesures communautaires (forums, tests indépendants)
- La norme WiFi supportée

### Gain d'antenne (dBi)
Même les fabricants de routeurs grand public (ASUS, TP-Link, Netgear) ne publient généralement pas ce chiffre dans leurs fiches produit. Les valeurs typiques observées :

| Catégorie | Gain typique |
|-----------|-------------|
| Box FAI compacte | 2.5 – 3.0 dBi |
| Système mesh (antennes internes) | 3.0 – 4.0 dBi |
| Routeur milieu de gamme (antennes externes) | 4.0 – 5.0 dBi |
| Routeur haut de gamme (antennes externes haute performance) | 5.0 – 6.0 dBi |

### Surface de couverture (area_m2)
Les valeurs annoncées par les fabricants sont obtenues en conditions idéales (espace ouvert, pas d'obstacles). En usage réel (murs, étages, interférences), appliquer un facteur de correction de **0.5 à 0.7**.

---

## Sources de référence pour enrichir la DB

| Source | Type de données |
|--------|----------------|
| [fccid.io](https://fccid.io) | Puissance Tx mesurée (RF Test Report) |
| [deviwiki.com](https://deviwiki.com) | Chipsets, config radio |
| [snbforums.com](https://snbforums.com) | Mesures communautaires réelles |
| Fiches produit constructeur | Standard, bandes, MIMO, couverture |
| [telecom-insiders.com](https://telecom-insiders.com) | Tests et comparatifs FR |

---

## Contenu du dataset v1.0

| Catégorie | Nombre |
|-----------|--------|
| Routeurs marché | 13 |
| Box FAI France | 8 |
| Systèmes mesh | 5 |
| **Total** | **26** |

### Répartition par standard WiFi
- WiFi 5 : 1 (Livebox 5)
- WiFi 6 : 12
- WiFi 6E : 7
- WiFi 7 : 6
