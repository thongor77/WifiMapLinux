"""
Export service — V2.3.

PNG : plan + heatmap overlay + bannière annotée.
PDF : page de résumé + une page par étage (heatmap mesurée).
"""
from __future__ import annotations

from datetime import date as _date
from pathlib import Path

import numpy as np

from .interpolation import grid_to_rgba

_BANNER_H = 72


# ── Fonts ─────────────────────────────────────────────────────────────────────

def _font(size: int):
    from PIL import ImageFont
    for path in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/TTF/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/OTF/SFNSDisplay.otf",
    ):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


# ── Internal helpers ──────────────────────────────────────────────────────────

def _compose(plan_path: str, grid: np.ndarray | None) -> "PIL.Image.Image":
    """Open floor plan, alpha-composite heatmap overlay, return RGB image."""
    from PIL import Image
    base = Image.open(plan_path).convert("RGBA")
    if grid is not None:
        H, W = grid.shape
        rgba = grid_to_rgba(grid)
        overlay = Image.frombytes("RGBA", (W, H), rgba.tobytes())
        overlay = overlay.resize((base.width, base.height), Image.LANCZOS)
        base = Image.alpha_composite(base, overlay)
    return base.convert("RGB")


def _rssi_stats(grid: np.ndarray | None) -> tuple[float, float, float] | None:
    if grid is None:
        return None
    valid = grid[~np.isnan(grid)]
    return (float(valid.min()), float(valid.mean()), float(valid.max())) if len(valid) else None


def _stats_str(grid: np.ndarray | None) -> str:
    s = _rssi_stats(grid)
    if s is None:
        return "Aucune mesure"
    return f"min {s[0]:.0f} dBm  ·  moy {s[1]:.0f} dBm  ·  max {s[2]:.0f} dBm"


def _banner(width: int, title: str, subtitle: str) -> "PIL.Image.Image":
    from PIL import Image, ImageDraw
    img = Image.new("RGB", (width, _BANNER_H), (238, 238, 248))
    draw = ImageDraw.Draw(img)
    draw.line([(0, 0), (width, 0)], fill=(180, 180, 215), width=2)
    draw.text((14, 8),  title,             font=_font(17), fill=(20, 20, 60))
    draw.text((14, 34), subtitle,          font=_font(12), fill=(80, 80, 120))
    draw.text((14, 54), str(_date.today()), font=_font(11), fill=(140, 140, 170))
    return img


# ── Public API ────────────────────────────────────────────────────────────────

def render_floor_image(
    plan_path: str,
    grid: np.ndarray | None,
    building_name: str,
    floor_name: str,
    ssid_label: str,
    measurement_count: int,
    target_w: int | None = None,
) -> "PIL.Image.Image":
    """
    Compose floor plan + heatmap overlay and append an annotation banner.

    target_w : if set, scale the plan to this width (preserving aspect ratio).
    """
    from PIL import Image
    base = _compose(plan_path, grid)
    if target_w and base.width != target_w:
        ratio = target_w / base.width
        base = base.resize((target_w, max(1, int(base.height * ratio))), Image.LANCZOS)

    ssid_str = ssid_label or "Tous réseaux"
    subtitle = (
        f"SSID : {ssid_str}  ·  {measurement_count} point(s)  ·  {_stats_str(grid)}"
    )
    banner = _banner(base.width, f"{building_name} — {floor_name}", subtitle)

    page = Image.new("RGB", (base.width, base.height + _BANNER_H), (255, 255, 255))
    page.paste(base, (0, 0))
    page.paste(banner, (0, base.height))
    return page


def export_floor_png(
    output_path: Path,
    plan_path: str,
    grid: np.ndarray | None,
    building_name: str,
    floor_name: str,
    ssid_label: str,
    measurement_count: int,
) -> None:
    """Export annotated floor plan as PNG."""
    img = render_floor_image(
        plan_path, grid, building_name, floor_name, ssid_label, measurement_count
    )
    img.save(str(output_path), "PNG")


def export_building_pdf(
    output_path: Path,
    building_name: str,
    floors: list[dict],
    ssid_label: str = "",
) -> None:
    """
    Export a multi-page PDF coverage report.

    floors : list of dicts, each with keys:
        name           (str)
        plan_path      (str | None)
        grid           (np.ndarray | None)
        measurement_count (int)
    """
    from PIL import Image

    TARGET_W = 1200
    pages: list[Image.Image] = [_summary_page(building_name, floors, TARGET_W)]

    for f in floors:
        if not f.get("plan_path"):
            continue
        img = render_floor_image(
            f["plan_path"],
            f.get("grid"),
            building_name,
            f["name"],
            ssid_label,
            f.get("measurement_count", 0),
            target_w=TARGET_W,
        )
        pages.append(img)

    if not pages:
        return
    pages[0].save(
        str(output_path), "PDF",
        save_all=True,
        append_images=pages[1:],
        resolution=150,
    )


def _summary_page(building_name: str, floors: list[dict], width: int) -> "PIL.Image.Image":
    """Text-only summary page with per-floor RSSI stats table."""
    from PIL import Image, ImageDraw

    row_h = 44
    top_h = 220
    page_h = max(800, top_h + len(floors) * row_h + 80)
    page = Image.new("RGB", (width, page_h), (255, 255, 255))
    draw = ImageDraw.Draw(page)

    # Header
    draw.text((50, 50),  "Rapport de couverture Wi-Fi",   font=_font(28), fill=(20, 20, 60))
    draw.text((50, 105), f"Maison : {building_name}",      font=_font(15), fill=(60, 60, 110))
    draw.text((50, 135), f"Généré le {_date.today()}",     font=_font(13), fill=(120, 120, 160))

    # Table
    cols   = [50,  230, 410, 580, 750]
    labels = ["Étage", "Points", "RSSI min", "RSSI moyen", "RSSI max"]
    y = top_h
    for x, lbl in zip(cols, labels):
        draw.text((x, y), lbl, font=_font(14), fill=(30, 30, 80))
    y += 24
    draw.line([(50, y), (width - 50, y)], fill=(160, 160, 200), width=1)
    y += 12

    for i, f in enumerate(floors):
        s = _rssi_stats(f.get("grid"))
        row = [
            f["name"],
            str(f.get("measurement_count", 0)),
            f"{s[0]:.0f} dBm" if s else "—",
            f"{s[1]:.0f} dBm" if s else "—",
            f"{s[2]:.0f} dBm" if s else "—",
        ]
        bg = (248, 248, 255) if i % 2 == 0 else (255, 255, 255)
        draw.rectangle([(50, y - 4), (width - 50, y + row_h - 8)], fill=bg)
        for x, val in zip(cols, row):
            draw.text((x, y), val, font=_font(13), fill=(50, 50, 80))
        y += row_h

    return page
