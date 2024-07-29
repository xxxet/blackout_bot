from sqlalchemy import Integer
from sqlalchemy.orm import mapped_column, Mapped

from src.sql.models import Base


class Zone(Base):
    __tablename__ = "zones"
    zone_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zone_name: Mapped[str]
