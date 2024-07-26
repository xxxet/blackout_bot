from sqlalchemy import Integer, ForeignKey, String
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.sql.models import Base
from src.sql.models.group import Group
from src.sql.models.user import User


class Subscription(Base):
    __tablename__ = "subscriptions"
    user_tg_id: Mapped[str] = mapped_column(
        String, ForeignKey("users.tg_id"), primary_key=True
    )
    group_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("groups.group_id"), primary_key=True
    )
    group: Mapped[Group] = relationship(Group)
    user: Mapped["User"] = relationship(back_populates="subs")
