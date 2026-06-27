"""
Save / load a complete WifiMapLinux project as a portable .wifimap archive.

Format: ZIP file containing
  project.db   — copy of the SQLite database with image_path stored as
                 "images/<floorplan_id><ext>" (relative, unique per floor)
  images/      — floor plan files renamed by their FloorPlan primary key
"""

import os
import sqlite3
import tempfile
import zipfile
from pathlib import Path

EXTENSION = ".wifimap"
_DB_ARCHIVE = "project.db"
_IMAGES_DIR = "images"


def save_project(zip_path: str | Path, db_path: Path) -> None:
    """Pack the current DB + floor plan images into a .wifimap archive."""
    zip_path = Path(zip_path)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT id, image_path FROM floorplan").fetchall()
    conn.close()

    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        src = sqlite3.connect(db_path)
        dst = sqlite3.connect(tmp_path)
        src.backup(dst)
        src.close()

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fp_id, img_path_str in rows:
                if not img_path_str:
                    continue
                img = Path(img_path_str)
                archive_name = f"{_IMAGES_DIR}/{fp_id}{img.suffix}"
                dst.execute(
                    "UPDATE floorplan SET image_path = ? WHERE id = ?",
                    (archive_name, fp_id),
                )
                if img.exists():
                    zf.write(img, archive_name)
            dst.commit()
            dst.close()
            zf.write(tmp_path, _DB_ARCHIVE)
    finally:
        os.unlink(tmp_path)


def load_project(zip_path: str | Path, data_dir: Path, db_path: Path) -> None:
    """Unpack a .wifimap archive and replace the current project data."""
    zip_path = Path(zip_path)
    images_dir = data_dir / _IMAGES_DIR
    images_dir.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = zf.namelist()
        if _DB_ARCHIVE not in names:
            raise ValueError(f"Invalid archive: {_DB_ARCHIVE} not found")

        for name in names:
            if name.startswith(f"{_IMAGES_DIR}/") and not name.endswith("/"):
                target = data_dir / name
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(name) as src, open(target, "wb") as dst:
                    dst.write(src.read())

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
            tmp_path = Path(tmp.name)
        try:
            with zf.open(_DB_ARCHIVE) as src, open(tmp_path, "wb") as dst:
                dst.write(src.read())

            conn = sqlite3.connect(tmp_path)
            rows = conn.execute(
                "SELECT id, image_path FROM floorplan"
            ).fetchall()
            for fp_id, rel_path in rows:
                if rel_path:
                    abs_path = str(data_dir / rel_path)
                    conn.execute(
                        "UPDATE floorplan SET image_path = ? WHERE id = ?",
                        (abs_path, fp_id),
                    )
            conn.commit()
            conn.close()

            src_conn = sqlite3.connect(tmp_path)
            dst_conn = sqlite3.connect(db_path)
            src_conn.backup(dst_conn)
            src_conn.close()
            dst_conn.close()
        finally:
            os.unlink(tmp_path)
