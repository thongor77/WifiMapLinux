from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .building import Building


class Floor(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    building_id: int = Field(foreign_key="building.id")
    index: int
    label: str
    height_m: float = Field(default=2.5)
    floor_attenuation_db: float = Field(default=12.0)
    offset_x_m: float = Field(default=0.0)
    offset_y_m: float = Field(default=0.0)

    building: Optional["Building"] = Relationship(back_populates="floors")
    floorplan: Optional["FloorPlan"] = Relationship(back_populates="floor")


class FloorPlan(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    floor_id: int = Field(foreign_key="floor.id", unique=True)
    image_path: str
    width_px: int
    height_px: int
    scale_px_per_m: Optional[float] = None
    cal_p1_x: Optional[int] = None
    cal_p1_y: Optional[int] = None
    cal_p2_x: Optional[int] = None
    cal_p2_y: Optional[int] = None
    cal_dist_m: Optional[float] = None

    floor: Optional[Floor] = Relationship(back_populates="floorplan")
