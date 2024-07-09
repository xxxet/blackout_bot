from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship, Mapped

from config import Base
from sql.models.group import Group
from sql.models.user import User


class Subscription(Base):
    __tablename__ = 'subscriptions'
    sub_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))
    group_id = Column(Integer, ForeignKey("groups.group_id"))
    group = relationship(Group)
    user: Mapped["User"] = relationship(back_populates="subs")

