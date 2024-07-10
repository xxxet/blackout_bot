from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped

from config import Base
from sql.models.group import Group
from sql.models.user import User


class Subscription(Base):
    __tablename__ = 'subscriptions'
    user_tg_id = Column(String, ForeignKey("users.tg_id"), primary_key=True)
    group_id = Column(Integer, ForeignKey("groups.group_id"), primary_key=True)
    group = relationship(Group)
    user: Mapped["User"] = relationship(back_populates="subs")
