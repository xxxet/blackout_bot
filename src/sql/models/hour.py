from sqlalchemy import Integer, ForeignKey
from sqlalchemy.orm import relationship, mapped_column, Mapped

from src.sql.models import Base

from src.sql.models.day import Day
from src.sql.models.group import Group
from src.sql.models.zone import Zone


class Hour(Base):
    __tablename__ = "hours"
    hour_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_id: Mapped[int] = mapped_column(Integer, ForeignKey("days.day_id"))
    hour: Mapped[int]
    zone_id: Mapped[int] = mapped_column(Integer, ForeignKey("zones.zone_id"))
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("groups.group_id"))
    day: Mapped[Day] = relationship(Day)
    zone: Mapped[Zone] = relationship(Zone)
    group: Mapped[Group] = relationship(Group)
