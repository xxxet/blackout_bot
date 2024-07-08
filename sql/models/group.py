from sqlalchemy import Column, Integer, String, Boolean

from config import Base


class Group(Base):
    __tablename__ = 'groups'
    group_id = Column(Integer, primary_key=True)
    custom = Column(Boolean)
    group_name = Column(String)
