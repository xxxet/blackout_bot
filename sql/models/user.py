from typing import List

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship, Mapped

from config import Base


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    tg_id = Column(String)
    show_help = Column(Boolean)
    subs: Mapped[List["Subscription"]] = relationship(back_populates="user")
