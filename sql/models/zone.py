from sqlalchemy import Column, Integer, String

from sql.config import Base


class Zone(Base):
    __tablename__ = 'zones'
    zone_id = Column(Integer, primary_key=True)
    zone_name = Column(String)
