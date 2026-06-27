from typing import Optional

from sqlmodel import Field, SQLModel


class AccessPoint(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    floor_id: int = Field(foreign_key="floor.id")
    x_px: float
    y_px: float
    label: str = Field(default="AP")
    tx_power_dbm: float = Field(default=20.0)
    frequency_mhz: float = Field(default=2437.0)
