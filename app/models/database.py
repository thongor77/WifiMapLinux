from pathlib import Path
from sqlmodel import create_engine, Session, SQLModel

_engine = None
DATA_DIR: Path = Path("data")


def init_db(data_dir: Path) -> None:
    global _engine, DATA_DIR
    DATA_DIR = data_dir
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    _engine = create_engine(f"sqlite:///{DATA_DIR / 'wifimaplinux.db'}")
    from app.models.building import Building  # noqa: register with metadata
    from app.models.floor import Floor, FloorPlan  # noqa
    from app.models.measurement import MeasurementPoint, MeasurementScan  # noqa
    from app.models.access_point import AccessPoint  # noqa
    SQLModel.metadata.create_all(_engine)


def get_session() -> Session:
    return Session(_engine)


def dispose_engine() -> None:
    """Close all pooled connections (call before overwriting the DB file)."""
    if _engine is not None:
        _engine.dispose()


def db_path() -> Path:
    return DATA_DIR / "wifimaplinux.db"
