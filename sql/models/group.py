from sqlalchemy import Column, Integer, String

from sql.config import Base


class Group(Base):
    __tablename__ = 'groups'
    group_id = Column(Integer, primary_key=True)
    group_name = Column(String)
