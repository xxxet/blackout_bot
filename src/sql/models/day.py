from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import mapped_column, Mapped

from src.sql.models import Base


class Day(Base):
    __tablename__ = "days"
    day_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    day_name: Mapped[str]
