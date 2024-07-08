from sqlalchemy import Column, Integer, String

from config import Base


class Day(Base):
    __tablename__ = 'days'
    day_id = Column(Integer, primary_key=True)
    day_name = Column(String)
