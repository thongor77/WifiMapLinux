from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from .floor import Floor


class Building(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)

    floors: List["Floor"] = Relationship(back_populates="building")
