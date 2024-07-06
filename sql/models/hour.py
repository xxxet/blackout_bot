
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from sql.config import Base
from sql.models.day import Day
from sql.models.group import Group
from sql.models.zone import Zone


class Hour(Base):
    __tablename__ = 'hours'
    hour_id = Column(Integer, primary_key=True)
    day_id = Column(Integer, ForeignKey('days.day_id'))
    hour = Column(Integer)
    zone_id = Column(Integer, ForeignKey('zones.zone_id'))
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    day = relationship(Day)
    zone = relationship(Zone)
    group = relationship(Group)
