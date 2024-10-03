import pytest
from assertpy import assert_that
from freezegun import freeze_time

import config
from src.sql.remind_obj import RemindObj
from src.sql.sql_time_finder import SqlTimeFinder
from tests.conftest import to_datetime, GROUP_5


class TestTimeFinder:

    @pytest.fixture()
    def remind_23_45(self) -> RemindObj:
        return RemindObj(
            old_zone="white",
            new_zone="black",
            group=GROUP_5,
            notify_now=False,
            remind_time=to_datetime("08-19-2024 23:45:00 +0300"),
            change_time=to_datetime("08-20-2024 00:00:00 +0300"),
        )

    @pytest.fixture()
    def remind_20_45(self) -> RemindObj:
        return RemindObj(
            old_zone="grey",
            new_zone="white",
            group=GROUP_5,
            notify_now=False,
            remind_time=to_datetime("08-19-2024 20:45:00 +0300"),
            change_time=to_datetime("08-19-2024 21:00:00 +0300"),
        )

    @freeze_time("08-19-2024 20:44:59 +0300")
    def test_notify_before_remind_time(self, remind_20_45: RemindObj) -> None:
        """Test notification before 'notify before time'"""
        tf = SqlTimeFinder(GROUP_5, config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15)
        assert_that(remind.__dict__).is_equal_to(remind_20_45.__dict__)

    @freeze_time("08-19-2024 21:00:00 +0300")
    def test_notify_zone_starts(self, remind_23_45: RemindObj) -> None:
        """Test notification before 'notify before time'"""
        tf = SqlTimeFinder(GROUP_5, config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15)
        assert_that(remind.__dict__).is_equal_to(remind_23_45.__dict__)

    @freeze_time("08-19-2024 20:45:00 +0300")
    def test_notify_in_next_hour(self, remind_23_45: RemindObj) -> None:
        """Test notification for the next hour"""
        tf = SqlTimeFinder(GROUP_5, config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15, hours_add=1)
        assert_that(remind.__dict__).is_equal_to(remind_23_45.__dict__)

    @pytest.mark.parametrize(
        "time_to_freeze", ["08-19-2024 20:45:00 +0300", "08-19-2024 20:59:59 +0300"]
    )
    def test_notify_in_remind_period(
        self, time_to_freeze: str, remind_20_45: RemindObj
    ) -> None:
        """Test notification in 'notify before range', notify_now should be True"""
        tf = SqlTimeFinder("%s" % GROUP_5, config.tz)
        tf.read_schedule()
        with freeze_time(time_to_freeze):
            remind = tf.find_next_remind_time(15)
            remind_20_45.notify_now = True
            assert_that(remind.__dict__).is_equal_to(remind_20_45.__dict__)

    @freeze_time("08-18-2024 23:00:00 +0300")
    def test_end_of_week(self, remind_23_45: RemindObj) -> None:
        expected_remind = RemindObj(
            old_zone="white",
            new_zone="black",
            group=GROUP_5,
            notify_now=False,
            remind_time=to_datetime("08-18-2024 23:45:00 +0300"),
            change_time=to_datetime("08-19-2024 00:00:00 +0300"),
        )
        tf = SqlTimeFinder(GROUP_5, config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15)
        assert_that(remind.__dict__).is_equal_to(expected_remind.__dict__)
