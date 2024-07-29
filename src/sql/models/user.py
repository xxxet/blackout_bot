from typing import List

from sqlalchemy import String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.sql.models import Base


class User(Base):
    __tablename__ = "users"
    tg_id: Mapped[str] = mapped_column(String, primary_key=True)
    show_help: Mapped[bool]
    subs: Mapped[List["Subscription"]] = relationship(  # noqa
        back_populates="user", cascade="all, delete"
    )
