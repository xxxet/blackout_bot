from typing import List

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from config import Base


class User(Base):
    __tablename__ = 'users'
    tg_id = Column(String, primary_key=True)
    show_help = Column(Boolean)
    subs: Mapped[List["Subscription"]] = relationship(back_populates="user", cascade="all, delete")
