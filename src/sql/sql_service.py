from datetime import time
from typing import List

from sqlalchemy import func, and_, over
from sqlalchemy.orm import Session, joinedload

import config
from src.sql.models.day import Day
from src.sql.models.group import Group
from src.sql.models.hour import Hour
from src.sql.models.subscription import Subscription
from src.sql.models.user import User
from src.sql.models.zone import Zone


class ZoneRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_zone(self, name: str) -> Zone:
        return self.db.query(Zone).filter(Zone.zone_name == name).first()

    def add(self, name: str) -> None:
        zone = Zone(zone_name=name)
        self.db.add(zone)
        self.db.commit()
        self.db.refresh(zone)


class GroupRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_group(self, name: str) -> Group:
        return self.db.query(Group).filter(Group.group_name == name).first()

    def get_groups(self) -> list[Group]:
        return self.db.query(Group).all()

    def add(self, name: str, custom: bool) -> None:
        grp = Group(group_name=name, custom=custom)
        self.db.add(grp)
        self.db.commit()
        self.db.refresh(grp)


class SubsRepo:
    def __init__(self, db: Session):
        self.db = db

    def delete(self, sub: Subscription) -> None:
        self.db.delete(sub)
        self.db.commit()
        self.db.flush()

    def get_subs(self) -> list[Subscription]:
        return self.db.query(Subscription).options(joinedload(Subscription.group)).all()

    def get_subs_for_tgid(self, tg_id: int) -> list[Subscription]:
        return (
            self.db.query(Subscription)
            .filter(Subscription.user_tg_id == tg_id)
            .options(joinedload(Subscription.group))
            .all()
        )

    def get_subs_for_user(self, user: User) -> List[Subscription]:
        if user is None:
            return []
        return (
            self.db.query(Subscription)
            .filter(Subscription.user_tg_id == user.tg_id)
            .options(joinedload(Subscription.group))
            .all()
        )

    def get_subs_for_user_grp(self, user: User, grp: Group) -> List[Subscription]:
        if user is None or grp is None:
            return []
        return (
            self.db.query(Subscription)
            .filter(
                Subscription.user_tg_id == user.tg_id,
                Subscription.group_id == grp.group_id,
            )
            .options(joinedload(Subscription.group))
            .all()
        )

    def add(self, user: User, grp: Group) -> None:
        sub = Subscription(user_tg_id=user.tg_id, group_id=grp.group_id)
        self.db.add(sub)
        self.db.commit()
        self.db.refresh(sub)


class UsersRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_users(self) -> list[User]:
        return self.db.query(User).options(joinedload(User.subs)).all()

    def get_user(self, tg_id: int) -> User:
        return (
            self.db.query(User)
            .filter(User.tg_id == tg_id)
            .options(joinedload(User.subs))
            .first()
        )

    def add(self, tg_id: int, show_help: bool = False) -> None:
        user = User(tg_id=tg_id, show_help=show_help)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

    def delete(self, user: User) -> None:
        self.db.delete(user)
        self.db.commit()
        self.db.flush()


class DayRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_day(self, name: str) -> Day:
        return self.db.query(Day).filter(Day.day_name == name).first()

    def get(self, day_id: int) -> Day:
        return self.db.query(Day).filter(Day.day_id == day_id).first()

    def add(self, name: str) -> None:
        day = Day(day_name=name)
        self.db.add(day)
        self.db.commit()
        self.db.refresh(day)


class HourRepo:
    def __init__(self, db: Session):
        self.db = db

    def get_hours_for_day_group(self, day: Day, grp: Group) -> list[Hour]:
        return (
            self.db.query(Hour)
            .filter(Hour.day_id == day.day_id, Group.group_name == grp.group_name)
            .all()
        )

    def get_hours_for_day(self, day: Day) -> list[Hour]:
        return self.db.query(Hour).filter(Hour.day_id == day.day_id).all()

    def get_hours_for_group(self, group: Group) -> list[Hour]:
        return (
            self.db.query(Hour)
            .filter(Hour.group_id == group.group_id)
            .options(joinedload(Hour.zone), joinedload(Hour.day))
        ).all()

    def add(self, hour: int, zone: Zone, day: Day, group: Group) -> bool:
        hour = Hour(hour=hour, zone=zone, day=day, group=group)
        self.db.add(hour)
        self.db.commit()
        self.db.refresh(hour)
        return True


class SqlService:

    @staticmethod
    def delete_subs_for_user_group(tg_id: int, group_name: str) -> None:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            subs_repo = SubsRepo(session)
            user_repo = UsersRepo(session)
            group_repo = GroupRepo(session)
            group = group_repo.get_group(group_name)
            user = user_repo.get_user(tg_id)
            subs = subs_repo.get_subs_for_user_grp(user, group)
            for sub in subs:
                subs_repo.delete(sub)

    @staticmethod
    def delete_no_sub_user(tg_id: int) -> None:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_repo = UsersRepo(session)
            subs_repo = SubsRepo(session)
            user = user_repo.get_user(tg_id)
            if subs_repo.get_subs_for_user(user) == 0:
                user_repo.delete(user)

    @staticmethod
    def delete_user_with_subs(tg_id: int) -> None:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_repo = UsersRepo(session)
            user = user_repo.get_user(tg_id)
            if user is not None:
                user_repo.delete(user)

    @staticmethod
    def subscribe_user(tg_id: int, group_name: str) -> bool:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_repo = UsersRepo(session)
            subs_repo = SubsRepo(session)
            grp_repo = GroupRepo(session)
            user = user_repo.get_user(tg_id)
            if user is None:
                user = user_repo.add(tg_id)
            grp = grp_repo.get_group(group_name)
            if grp is None:
                return False
            ex_sub = subs_repo.get_subs_for_user_grp(user, grp)
            if len(ex_sub) == 0:
                subs_repo.add(user, grp)
            return True

    @staticmethod
    def get_all_subs() -> list[Subscription]:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            subs_repo = SubsRepo(session)
            return subs_repo.get_subs()

    @staticmethod
    def get_all_users() -> list[User]:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_repo = UsersRepo(session)
            return user_repo.get_users()

    @staticmethod
    def get_all_groups() -> list[Group]:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            group_repo = GroupRepo(session)
            return group_repo.get_groups()

    @staticmethod
    def update_user_help(tg_id: int, show_help: bool) -> None:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            user_repo = UsersRepo(session)
            user = user_repo.get_user(tg_id)
            user.show_help = show_help
            session.commit()

    @staticmethod
    def get_subs_for_user(tg_id: int) -> list[Subscription]:
        session_maker = config.get_session_maker()
        with session_maker() as session:
            subs_repo = SubsRepo(session)
            user_repo = UsersRepo(session)
            return subs_repo.get_subs_for_user(user_repo.get_user(tg_id))

    @staticmethod
    def get_schedule_for(day: str, group: str) -> list[str]:
        """
        query:
            select zone_name, hour, count(*)
            from (
            select
                    h.*, z.zone_name,
                    (row_number() over(order by h.hour_id)  -
                    row_number() over(partition by h.zone_id order by h.hour_id)  ) as grp
                    from hours h
                    inner join zones z on h.zone_id = z.zone_id
                        inner join days d on h.day_id = d.day_id
                        inner join groups g on h.group_id = g.group_id
                        WHERE d.day_name = 'Monday' and g.group_name='group5'
                        ) hours_groups
            group by grp, zone_id order by hour

        :param day:
        :param group:
        """
        session_maker = config.get_session_maker()
        with session_maker() as session:
            sub_q = (
                session.query(
                    Zone.zone_name,
                    Group.group_name,
                    Hour,
                    (
                        over(func.row_number(), order_by=Hour.hour_id)
                        - over(
                            func.row_number(),
                            order_by=Hour.hour_id,
                            partition_by=Hour.zone_id,
                        )
                    ).label("grp_zone"),
                )
                .select_from(Hour)
                .join(Zone, Zone.zone_id == Hour.zone_id)
                .join(Group, Group.group_id == Hour.group_id)
                .join(Day, Day.day_id == Hour.day_id)
                .filter(and_(Day.day_name == day, Group.group_name == group))
                .subquery()
            )
            outage_hours_query = (
                session.query(sub_q.c, func.count().label("outage_hours"))
                .select_from(sub_q)
                .group_by("grp_zone", sub_q.c.zone_id)
                .order_by(sub_q.c.hour)
            )
            outage_hours_result = outage_hours_query.all()
            return [
                f"{time(hour=row.hour, tzinfo=config.tz).strftime("%H:%M")}: {row.zone_name}"
                for row in outage_hours_result
            ]
