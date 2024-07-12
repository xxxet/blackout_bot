from typing import List

from sqlalchemy.orm import Session, joinedload

import config
from sql.models.day import Day
from sql.models.group import Group
from sql.models.hour import Hour
from sql.models.subscription import Subscription
from sql.models.user import User
from sql.models.zone import Zone


class ZoneService:
    def __init__(self, db: Session):
        self.db = db

    def get_zone(self, name: str):
        return self.db.query(Zone).filter(Zone.zone_name == name).first()

    def add(self, name: str):
        zone = Zone(zone_name=name)
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)


class GroupService:
    def __init__(self, db: Session):
        self.db = db

    def get_group(self, name: str) -> Group:
        return self.db.query(Group).filter(Group.group_name == name).first()

    def add(self, name: str, custom: bool):
        grp = Group(group_name=name, custom=custom)
        self.db.add(grp)
        self.db.commit()
        self.db.refresh(grp)


class SubsService:
    def __init__(self, db: Session):
        self.db = db

    def delete(self, sub: Subscription):
        self.db.delete(sub)
        self.db.commit()
        self.db.flush()

    def get_subs(self) -> List[Subscription]:
        return (self.db.query(Subscription)
                .options(joinedload(Subscription.group)).all())

    def get_subs_for_tgid(self, tgid: str) -> List[Subscription]:
        return (self.db.query(Subscription).filter(Subscription.user_tg_id == tgid)
                .options(joinedload(Subscription.group)).all())

    def get_subs_for_user(self, user: User) -> List[Subscription]:
        if user is None:
            return []
        return (self.db.query(Subscription).filter(Subscription.user_tg_id == user.tg_id)
                .options(joinedload(Subscription.group)).all())

    def get_subs_for_user_grp(self, user: User, grp: Group) -> List[Subscription]:
        if user is None or grp is None:
            return []
        return (self.db.query(Subscription).filter(Subscription.user_tg_id == user.tg_id,
                                                   Subscription.group_id == grp.group_id)
                .options(joinedload(Subscription.group)).all())

    def add(self, user: User, grp: Group):
        ex_sub = self.get_subs_for_user_grp(user, grp)
        if len(ex_sub) == 0:
            sub = Subscription(user_tg_id=user.tg_id, group_id=grp.group_id)
            self.db.add(sub)
            self.db.commit()
            self.db.refresh(sub)
            return sub
        else:
            return ex_sub


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, tg_id: str):
        return self.db.query(User).filter(User.tg_id == tg_id).options(joinedload(User.subs)).first()

    def add(self, tg_id: str, show_help=False):
        ex_user = self.get_user(tg_id)
        if ex_user is None:
            user = User(tg_id=tg_id, show_help=show_help)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        else:
            return ex_user

    def delete(self, user: User):
        if user is None:
            return
        self.db.delete(user)
        self.db.commit()
        self.db.flush()


class DayService:
    def __init__(self, db: Session):
        self.db = db

    def get_day(self, name: str):
        return self.db.query(Day).filter(Day.day_name == name).first()

    def get(self, day_id: int):
        return self.db.query(Day).filter(Day.day_id == day_id).first()

    def add(self, name: str):
        day = Day(day_name=name)
        self.db.add(day)
        self.db.commit()
        self.db.refresh(day)


class HourService:
    def __init__(self, db: Session):
        self.db = db

    def get_hours_for_day_group(self, day: Day, grp: Group):
        return self.db.query(Hour).filter(Hour.day_id == day.day_id,
                                          Group.group_name == grp.group_name)

    def get_hours_for_day(self, day: Day):
        return self.db.query(Hour).filter(Hour.day_id == day.day_id).all()

    def get_hours_for_group(self, group: Group):
        return (self.db.query(Hour).filter(Hour.group_id == group.group_id)
                .options(joinedload(Hour.zone), joinedload(Hour.day))).all()

    def add(self, hour: int, zone: Zone, day: Day, group: Group):
        hour = Hour(hour=hour, zone=zone,
                    day=day, group=group)
        self.db.add(hour)
        self.db.commit()
        self.db.refresh(hour)


class SqlOperationsFacade:

    @staticmethod
    def get_subs_for_user_group(tgid: str, group_name: str):
        session_maker = config.get_session_maker()
        with session_maker() as session:
            subs_serv = SubsService(session)
            user_serv = UserService(session)
            group_serv = GroupService(session)
            group = group_serv.get_group(group_name)
            user = user_serv.get_user(tgid)
            return subs_serv.get_subs_for_user_grp(user, group)
