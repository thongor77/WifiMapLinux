# WifiMapLinux — Data Models

> Last updated: 2026-06-27

---

## Overview

```
Building (House)
└── Floor [1..N]
    ├── FloorPlan [0..1]
    ├── AccessPoint [0..N]
    └── MeasurementPoint [0..N]
            └── MeasurementScan [1..N]
```

---

## Building

Top-level container. Groups all floors of a house.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `name` | str | Display name (e.g. "Main House") |
| `address` | str? | Optional address (not geocoded) |

---

## Floor

Represents one physical level of the house.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `building_id` | int FK | Parent house |
| `index` | int | Level: -1=basement, 0=ground floor, 1=1st, 2=2nd… |
| `label` | str | Display label (e.g. "Ground Floor") |
| `height_m` | float | Ceiling height in metres (e.g. 2.5) |
| `floor_attenuation_db` | float | Slab penetration attenuation (default: 12 dB — ADR-004) |
| `offset_x_m` | float | X offset in metres relative to ground floor (XY alignment) |
| `offset_y_m` | float | Y offset in metres relative to ground floor (XY alignment) |

**Notes:**
- `height_m` is used to compute `dz` in 3D propagation
- `floor_attenuation_db` models the slab between this floor and the one below
- `offset_x_m / offset_y_m` enable alignment of plans with different sizes (ADR-003)
- Stacking order is determined by `index` (ascending = bottom to top)

---

## FloorPlan

2D plan imported for a floor. 1:1 relationship with Floor.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `floor_id` | int FK unique | Associated floor |
| `image_path` | str | Local path to the PNG file |
| `width_px` | int | Plan width in pixels |
| `height_px` | int | Plan height in pixels |
| `scale_px_per_m` | float? | Calibration factor (null = not calibrated) |
| `cal_p1_x`, `cal_p1_y` | int? | First calibration point (pixels) |
| `cal_p2_x`, `cal_p2_y` | int? | Second calibration point (pixels) |
| `cal_dist_m` | float? | Real-world distance between the two points (metres) |

**Note:** while `scale_px_per_m` is null, simulation and interpolation are disabled.

---

## AccessPoint

Virtual AP (simulation).

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `floor_id` | int FK | Floor where the AP is placed |
| `x_px` | float | X position on the plan (pixels) |
| `y_px` | float | Y position on the plan (pixels) |
| `label` | str | Display name (e.g. "AP Living Room") |
| `tx_power_dbm` | float | Transmit power (default: 20 dBm) |
| `frequency_mhz` | float | Frequency in MHz (default: 2437 — 2.4 GHz ch 6) |

---

## MeasurementPoint

Physical location where the user performed a Wi-Fi scan.

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `floor_id` | int FK | Floor where the scan was performed |
| `x_px` | float | X position on the plan (pixels) |
| `y_px` | float | Y position on the plan (pixels) |
| `label` | str? | Optional label (e.g. "Kitchen", "1st-floor hallway") |

---

## MeasurementScan

Wi-Fi network detected at a measurement point.
One measurement point contains N scans (one per detected network).

| Field | Type | Description |
|-------|------|-------------|
| `id` | int PK | Primary key |
| `measurement_point_id` | int FK | Parent measurement point |
| `ssid` | str | Network name |
| `bssid` | str | Access point MAC address |
| `signal_dbm` | int | Signal level in dBm (e.g. -62) |
| `channel` | int | Wi-Fi channel |
| `frequency_mhz` | int | Frequency in MHz (e.g. 5180) |

---

## Relationships

```
Building      1 ──< Floor             N
Floor         1 ──< FloorPlan         (0 or 1)
Floor         1 ──< AccessPoint       N
Floor         1 ──< MeasurementPoint  N
MeasurementPoint 1 ──< MeasurementScan N
```
