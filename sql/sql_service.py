from datetime import time
from typing import List

from sqlalchemy import func, and_, over
from sqlalchemy.orm import Session, joinedload

import config
from sql.models.day import Day
from sql.models.group import Group
from sql.models.hour import Hour
from sql.models.subscription import Subscription
from sql.models.user import User
from sql.models.zone import Zone


class ZoneRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_zone(self, name: str):
        return self.db.query(Zone).filter(Zone.zone_name == name).first()

    def add(self, name: str):
        zone = Zone(zone_name=name)
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)


class GroupRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_group(self, name: str) -> Group:
        return self.db.query(Group).filter(Group.group_name == name).first()

    def get_groups(self) -> List[Group]:
        return self.db.query(Group).all()

    def add(self, name: str, custom: bool):
        grp = Group(group_name=name, custom=custom)
        self.db.add(grp)
        self.db.commit()
        self.db.refresh(grp)


class SubsRepo:
    def __init__(self, db: Session):
        self.db = db

    def delete(self, sub: Subscription):
        self.db.delete(sub)
        self.db.commit()
        self.db.flush()

    def get_subs(self) -> List[Subscription]:
        return (self.db.query(Subscription)
                .options(joinedload(Subscription.group)).all())

    def get_subs_for_tgid(self, tg_id: int) -> List[Subscription]:
        return (self.db.query(Subscription).filter(Subscription.user_tg_id == tg_id)
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

    def add(self, user: User, grp: Group) -> bool:
        ex_sub = self.get_subs_for_user_grp(user, grp)
        if len(ex_sub) == 0:
            sub = Subscription(user_tg_id=user.tg_id, group_id=grp.group_id)
            self.db.add(sub)
            self.db.commit()
            self.db.refresh(sub)
            return True
        return False


class UsersRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self) -> List[User]:
        return self.db.query(User).options(joinedload(User.subs)).all()

    def get_user(self, tg_id: int) -> User:
        return self.db.query(User).filter(User.tg_id == tg_id).options(joinedload(User.subs)).first()

    def add(self, tg_id: int, show_help=False):
        ex_user = self.get_user(tg_id)
        if ex_user is None:
            user = User(tg_id=tg_id, show_help=show_help)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        return ex_user

    def delete(self, user: User):
        if user is None:
            return
        self.db.delete(user)
        self.db.commit()
        self.db.flush()


class DayRepo:
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


class HourRepo:
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


class SqlService:

    @staticmethod
    def delete_subs_for_user_group(tg_id: int, group_name: str):
        session_maker = config.get_session_maker()
        with session_maker() as session:
            subs_serv = SubsRepo(session)
            user_serv = UsersRepo(session)
            group_serv = GroupRepo(session)
            group = group_serv.get_group(group_name)
            user = user_serv.get_user(tg_id)
            subs = subs_serv.get_subs_for_user_grp(user, group)
            for sub in subs:
                subs_serv.delete(sub)

    @staticmethod
    def delete_no_sub_user(tg_id: int):
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_serv = UsersRepo(session)
            subs_serv = SubsRepo(session)
            user = user_serv.get_user(tg_id)
            if subs_serv.get_subs_for_user(user) == 0:
                user_serv.delete(user)

    @staticmethod
    def delete_user_with_subs(tg_id: int):
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_serv = UsersRepo(session)
            user = user_serv.get_user(tg_id)
            user_serv.delete(user)

    @staticmethod
    def subscribe_user(tg_id: int, group_name: str):
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_serv = UsersRepo(session)
            subs_serv = SubsRepo(session)
            grp_serv = GroupRepo(session)
            user = user_serv.add(tg_id)
            grp = grp_serv.get_group(group_name)
            if grp is None:
                return False
            return subs_serv.add(user, grp)


    @staticmethod
    def get_all_subs():
        session_maker = config.get_session_maker()
        with session_maker() as session:
            subs_serv = SubsRepo(session)
            return subs_serv.get_subs()

    @staticmethod
    def get_all_users():
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_repo = UsersRepo(session)
            return user_repo.get_users()

    @staticmethod
    def get_all_groups() -> List[Group]:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            group_repo = GroupRepo(session)
            return group_repo.get_groups()

    @staticmethod
    def update_user_help(tg_id: int, show_help: bool):
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_serv = UsersRepo(session)
            user = user_serv.get_user(tg_id)
            user.show_help = show_help
            session.commit()

    @staticmethod
    def get_subs_for_user(tg_id: int):
        session_maker = config.get_session_maker()
        with session_maker() as session:
            subs_serv = SubsRepo(session)
            user_serv = UsersRepo(session)
            return subs_serv.get_subs_for_user(user_serv.get_user(tg_id))

    @staticmethod
    def get_schedule_for(day: str, group: str):
        """
        query:
                # select zone_name, hour, count(*)
                # from (
                # select
                #          h.*, z.zone_name,
                #     	(row_number() over(order by h.hour_id)  -
                #         row_number() over(partition by h.zone_id order by h.hour_id)  ) as grp
                #         from hours h
                #        	inner join zones z on h.zone_id = z.zone_id
                # 		inner join days d on h.day_id = d.day_id
                # 		inner join groups g on h.group_id = g.group_id
                # 		WHERE d.day_name = 'Monday' and g.group_name='group5'
                # 		) hours_groups
                # group by grp, zone_id order by hour

        :param day:
        :param group:
        """
        session_maker = config.get_session_maker()
        with (session_maker() as session):
            sub_q = session.query(
                Zone.zone_name, Group.group_name, Hour, (over(func.row_number(), order_by=Hour.hour_id) -
                                                         over(func.row_number(), order_by=Hour.hour_id,
                                                              partition_by=Hour.zone_id)).label('grp_zone')
            ).select_from(
                Hour
            ).join(
                Zone, Zone.zone_id == Hour.zone_id
            ).join(
                Group, Group.group_id == Hour.group_id
            ).join(
                Day, Day.day_id == Hour.day_id
            ).filter(
                and_(Day.day_name == day, Group.group_name == group)
            ).subquery()
            outage_hours_query = session.query(sub_q.c,
                                               func.count().label("outage_hours")).select_from(sub_q).group_by(
                "grp_zone", sub_q.c.zone_id).order_by(sub_q.c.hour)
            outage_hours_result = outage_hours_query.all()
            return [f"{time(hour=row.hour, tzinfo=config.tz).strftime("%H:%M")}: {row.zone_name}" for row in
                    outage_hours_result]
