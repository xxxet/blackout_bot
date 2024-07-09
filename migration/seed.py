import logging
import pathlib

from group_reader.read_group import ReadGroup
from config import get_session_maker, ZONES
from sql.models.day import Day
from sql.models.group import Group
from sql.models.hour import Hour
from sql.models.subscription import Subscription
from sql.models.user import User
from sql.models.zone import Zone
from sql.sql_service import DayService, ZoneService, GroupService, HourService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')


def seed_groups():
    days_of_week = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    session_maker = get_session_maker()
    with session_maker() as session:
        day_serv = DayService(session)
        # Insert days into Days table
        for day_name in days_of_week:
            day_serv.add(day_name)

        zone_serv = ZoneService(session)
        # Insert zones into Zones table
        for zone in ZONES:
            zone_serv.add(zone)

        group_serv = GroupService(session)
        # Insert groups into Groups table

        files = [f for f in pathlib.Path("resources").iterdir()
                 if f.is_file()]
        for file in files:
            group_serv.add(file.stem, custom=False)
            group = group_serv.get_group(file.stem)
            rg = ReadGroup(str(file))
            rg.extract()
            hour_serv = HourService(session)
            for day_index, row in enumerate(rg.outage_table):
                logging.info(f"adding {day_index} {row}")
                day_id = day_index + 1  # Day IDs start from 1 to 7
                day = day_serv.get(day_id)
                for hour, zone in enumerate(row):
                    zone = zone_serv.get_zone(zone)
                    hour_serv.add(hour, zone, day, group)

        session.commit()


def delete_groups():
    sesh = get_session_maker()
    with sesh() as session:
        session.query(Hour).delete()
        session.query(Zone).delete()
        session.query(Group).delete()
        session.query(Subscription).delete()
        session.query(User).delete()
        session.query(Day).delete()
        session.commit()


if __name__ == "__main__":
    seed_groups()
