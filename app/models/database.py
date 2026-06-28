from pathlib import Path
from sqlalchemy import text
from sqlalchemy.pool import NullPool
from sqlmodel import create_engine, Session, SQLModel


def _migrate(engine) -> None:
    """Add columns introduced after initial schema creation."""
    new_cols = [
        ("floor", "align_scale_x", "FLOAT NOT NULL DEFAULT 1.0"),
        ("floor", "align_scale_y", "FLOAT NOT NULL DEFAULT 1.0"),
    ]
    with engine.connect() as conn:
        for table, col, definition in new_cols:
            existing = {
                r[1] for r in conn.execute(
                    text(f"PRAGMA table_info({table})")
                ).fetchall()
            }
            if col not in existing:
                conn.execute(text(
                    f"ALTER TABLE {table} ADD COLUMN {col} {definition}"
                ))
        conn.commit()

_engine = None
DATA_DIR: Path = Path("data")


def init_db(data_dir: Path) -> None:
    global _engine, DATA_DIR
    DATA_DIR = data_dir
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    # NullPool: each Session opens its own connection and closes it on exit.
    # Avoids SQLAlchemy's SingletonThreadPool sharing one connection across
    # concurrent sessions (ap_panel, measurement_panel, heatmap, voxel all
    # open sessions simultaneously during floor selection).
    _engine = create_engine(
        f"sqlite:///{DATA_DIR / 'wifimaplinux.db'}",
        poolclass=NullPool,
    )
    from app.models.building import Building  # noqa: register with metadata
    from app.models.floor import Floor, FloorPlan  # noqa
    from app.models.measurement import MeasurementPoint, MeasurementScan  # noqa
    from app.models.access_point import AccessPoint  # noqa
    SQLModel.metadata.create_all(_engine)
    _migrate(_engine)


def get_session() -> Session:
    return Session(_engine)


def dispose_engine() -> None:
    """Close all pooled connections (call before overwriting the DB file)."""
    if _engine is not None:
        _engine.dispose()


def db_path() -> Path:
    return DATA_DIR / "wifimaplinux.db"


def clear_db() -> None:
    """Wipe all data by deleting and recreating the database file."""
    p = db_path()
    dispose_engine()
    if p.exists():
        p.unlink()
    # Remove WAL / SHM leftovers
    for suffix in ("-wal", "-shm"):
        leftover = p.parent / (p.name + suffix)
        if leftover.exists():
            leftover.unlink()
    init_db(DATA_DIR)
