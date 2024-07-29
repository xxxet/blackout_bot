from sqlalchemy import Integer
from sqlalchemy.orm import mapped_column, Mapped

from src.sql.models import Base


class Group(Base):
    __tablename__ = "groups"
    group_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    custom: Mapped[bool]
    group_name: Mapped[str]
