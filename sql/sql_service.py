import csv

from sqlalchemy.orm import Session, joinedload

from config import Base
from sql.models.day import Day
from sql.models.group import Group
from sql.models.hour import Hour
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

    def get_group(self, name: str):
        return self.db.query(Group).filter(Group.group_name == name).first()

    def add(self, name: str, custom: bool):
        grp = Group(group_name=name, custom=custom)
        self.db.add(grp)
        self.db.commit()
        self.db.refresh(grp)


class UserService:
    def __init__(self, db: Session):
        self.db = db

    def get_user(self, user_id: int):
        return self.db.query(User).filter(User.id == user_id).first()

    def add(self, tgid: str, group: Group):
        user = User(tg_id=tgid, group=group)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user


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


def seed_db():
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import create_engine
    # Days of the week
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    # session = get_db()

    engine = create_engine('sqlite:///blackout.db')
    Base.metadata.create_all(engine)
    session_maker = sessionmaker(bind=engine)
    session = session_maker()
    day_serv = DayService(session)

    # Insert days into Days table
    for day_name in days_of_week:
        day_serv.add(day_name)

    zone_serv = ZoneService(session)
    # Insert zones into Zones table
    for zone in ["black", "grey", "white"]:
        zone_serv.add(zone)

    group_serv = GroupService(session)
    # Insert groups into Groups table
    for grp in ["group_5"]:
        group_serv.add(grp)

    user_serv = UserService(session)
    group_5 = group_serv.get_group("group_5")
    user_serv.add("tg1", group_5)

    # Read CSV and populate the TimeSeries table
    with open('../group5.csv', newline='') as csvfile:
        csvreader = csv.reader(csvfile)
        headers = next(csvreader)  # Skip the header row
        hour_serv = HourService(session)
        for day_index, row in enumerate(csvreader):
            day_id = day_index + 1  # Day IDs start from 1 to 7
            day = day_serv.get(day_id)
            for hour, zone in enumerate(row):
                zone = zone_serv.get_zone(zone)
                hour_serv.add(hour, zone, day, group_5)
                # timeseries = Hours(day_id=day_id, hour=hour, zone=zone)
                # session.add(timeseries)

    session.close()


if __name__ == '__main__':
    seed_db()
