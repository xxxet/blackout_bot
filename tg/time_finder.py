import csv
from datetime import datetime
from datetime import timedelta

import pytz

from group_reader.read_group import ReadGroup


class TimeFinder:
    def __init__(self, group_table_path, timezone):
        self.csv_file = None
        self.group_table_path = group_table_path
        self.tz = pytz.timezone(timezone)
        self.rg = ReadGroup(self.group_table_path)
        self.outage_table = []

    def read_schedule(self):
        self.rg.extract_table()
        with open(self.rg.csv_table, mode='r') as file:
            for row in csv.DictReader(file):
                self.outage_table.append(row)

    def get_next_zone_change(self, curdatetime):
        now = curdatetime

        def look_for_change_in_day(start_hour, day_ind, zone_to_compare):
            day = self.outage_table[day_ind]
            for hour in range(start_hour, len(day)):
                if day.get(str(hour)) != zone_to_compare:
                    return hour
            return None

        def look_for_change_in_week(cur_day, start_h):
            start_zone = self.outage_table[cur_day].get(str(start_h))
            # from cur day to the last day in week
            for day_ind in range(cur_day, len(self.outage_table)):
                hour = look_for_change_in_day(start_h, day_ind, start_zone)
                if hour is not None:
                    return hour, day_ind
                start_h = 0
            # from 0 to cur day
            for day_ind in range(cur_day):
                hour = look_for_change_in_day(start_h, day_ind, start_zone)
                if hour is not None:
                    return hour, day_ind
                start_h = 0

        change_h, change_d = look_for_change_in_week(now.weekday(), now.hour)
        if change_d >= now.weekday():
            day_change = timedelta(days=change_d - now.weekday())
        else:
            day_change = timedelta(days=len(self.outage_table) - now.weekday() + change_d)
        new_time = now + day_change
        new_time = new_time.replace(hour=change_h, minute=0)
        new_zone = self.outage_table[new_time.weekday()].get(str(new_time.hour))
        return new_time, new_zone

    def find_next_remind_time(self):
        # now = datetime(2024, 6, 23, 23, 00, 00)
        now = datetime.now(tz=self.tz)
        change_time, new_zone = self.get_next_zone_change(now)
        diff = change_time - now
        if diff.total_seconds() / 60 <= 15:
            return now, f"Zone is going to change to {new_zone} at {change_time.strftime("%H:%M")}"
        else:
            return change_time - timedelta(
                minutes=15), f"Zone is going to change to {new_zone} at {change_time.strftime("%H:%M")}"


if __name__ == '__main__':
    tf = TimeFinder("../group5.png", 'Europe/Kyiv')
    tf.read_schedule()
    print(tf.find_next_remind_time())
    pass