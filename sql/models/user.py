from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship

from sql.config import Base
from sql.models.group import Group


class User(Base):
    __tablename__ = 'users'
    user_id = Column(Integer, primary_key=True)
    tg_id = Column(String)
    group_id = Column(Integer, ForeignKey('groups.group_id'))
    group = relationship(Group)
