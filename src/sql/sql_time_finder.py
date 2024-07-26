from datetime import datetime
from datetime import timedelta

from pytz.tzinfo import BaseTzInfo

from config import get_session_maker
from src.sql.models.hour import Hour
from src.sql.remind_obj import RemindObj
from src.sql.sql_service import HourRepo, GroupRepo


class SqlTimeFinder:
    def __init__(self, group_name: str, timezone: BaseTzInfo):
        self.group_name = group_name
        self.tz = timezone
        self.hours_in_week: list[Hour] = []

    def read_schedule(self) -> None:
        session_maker = get_session_maker()
        with session_maker() as session:
            grp = GroupRepo(session).get_group(self.group_name)
            self.hours_in_week = HourRepo(session).get_hours_for_group(grp)

    def get_hour(self, day: int, start_h: int) -> tuple[int, str]:
        hour_ind = day * 24 + start_h
        zone = self.hours_in_week[hour_ind].zone.zone_name
        return hour_ind, zone

    def __look_for_change_in_week(self, day: int, start_h: int) -> tuple[Hour, int]:
        cur_hour_ind, cur_zone = self.get_hour(day, start_h)
        # look for change from current hour to the end of the week
        for hour in self.hours_in_week[cur_hour_ind:]:
            if hour.zone.zone_name != cur_zone:
                return hour, self.hours_in_week.index(hour) - cur_hour_ind

        # look for change from start of the week to the current hour
        for hour in self.hours_in_week[:cur_hour_ind]:
            if hour.zone.zone_name != cur_zone:
                return hour, len(
                    self.hours_in_week
                ) - cur_hour_ind + self.hours_in_week.index(hour)
        raise ValueError("No change in zone found")

    def find_next_remind_time(
        self, notify_before: int = 0, time_delta: int = 0
    ) -> RemindObj:
        # now = datetime(2024, 7, 14, 21, 00, 00)
        now = datetime.now(tz=self.tz) + timedelta(minutes=time_delta)
        _, old_zone = self.get_hour(now.weekday(), now.hour)
        change_h, hours_to_change = self.__look_for_change_in_week(
            now.weekday(), now.hour
        )
        zone_change_time = now.replace(minute=0) + timedelta(hours=hours_to_change)
        new_zone = change_h.zone.zone_name
        diff = zone_change_time - now
        # if notif should be sent in less than notify_before, return remind time = now
        if diff.total_seconds() / 60 <= notify_before:
            return RemindObj(
                group=self.group_name,
                old_zone=old_zone,
                new_zone=new_zone,
                change_time=zone_change_time,
                remind_time=now,
            )
        return RemindObj(
            group=self.group_name,
            old_zone=old_zone,
            new_zone=new_zone,
            change_time=zone_change_time,
            remind_time=zone_change_time - timedelta(minutes=notify_before),
        )
