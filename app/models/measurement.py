from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .floor import Floor


class MeasurementPoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    floor_id: int = Field(foreign_key="floor.id")
    x_px: float
    y_px: float
    label: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    scans: List["MeasurementScan"] = Relationship(back_populates="point")


class MeasurementScan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    measurement_point_id: int = Field(foreign_key="measurementpoint.id")
    ssid: str
    bssid: str
    signal_dbm: int
    channel: int
    frequency_mhz: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    point: Optional[MeasurementPoint] = Relationship(back_populates="scans")
