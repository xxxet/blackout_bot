import pytest
from assertpy import assert_that, soft_assertions
from freezegun import freeze_time

import config
from src.sql.sql_time_finder import SqlTimeFinder
from tests import to_dateformat


class TestTimeFinder:

    @freeze_time("08-19-2024 20:44:59 +0300")
    def test_notify_before_remind_time(self) -> None:
        """Test notification before 'notify before time'"""
        tf = SqlTimeFinder("group5", config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15)
        with soft_assertions():
            assert_that(remind.notify_now).is_equal_to(False)
            assert_that(remind.new_zone).matches("white")
            assert_that(remind.old_zone).matches("grey")
            assert_that(to_dateformat(remind.change_time)).is_equal_to(
                "08-19-2024 21:00:00 +0300"
            )
            assert_that(to_dateformat(remind.remind_time)).is_equal_to(
                "08-19-2024 20:45:00 +0300"
            )

    @freeze_time("08-19-2024 21:00:00 +0300")
    def test_notify_zone_starts(self) -> None:
        """Test notification before 'notify before time'"""
        tf = SqlTimeFinder("group5", config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15)
        with soft_assertions():
            assert_that(remind.notify_now).is_equal_to(False)
            assert_that(remind.new_zone).matches("black")
            assert_that(remind.old_zone).matches("white")
            assert_that(to_dateformat(remind.change_time)).is_equal_to(
                "08-20-2024 00:00:00 +0300"
            )
            assert_that(to_dateformat(remind.remind_time)).is_equal_to(
                "08-19-2024 23:45:00 +0300"
            )

    @freeze_time("08-19-2024 20:45:00 +0300")
    def test_notify_in_next_hour(self) -> None:
        """Test notification for the next hour"""
        tf = SqlTimeFinder("group5", config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15, hours_add=1)
        with soft_assertions():
            assert_that(remind.notify_now).is_equal_to(False)
            assert_that(remind.new_zone).matches("black")
            assert_that(remind.old_zone).matches("white")
            assert_that(to_dateformat(remind.change_time)).is_equal_to(
                "08-20-2024 00:00:00 +0300"
            )
            assert_that(to_dateformat(remind.remind_time)).is_equal_to(
                "08-19-2024 23:45:00 +0300"
            )

    @pytest.mark.parametrize(
        "time_to_freeze", ["08-19-2024 20:45:00 +0300", "08-19-2024 20:59:59 +0300"]
    )
    def test_notify_in_remind_period(self, time_to_freeze: str) -> None:
        """Test notification in 'notify before range', notify_now should be True"""
        tf = SqlTimeFinder("group5", config.tz)
        tf.read_schedule()
        with freeze_time(time_to_freeze):
            remind = tf.find_next_remind_time(15)
            with soft_assertions():
                assert_that(remind.notify_now).is_equal_to(True)
                assert_that(remind.new_zone).matches("white")
                assert_that(remind.old_zone).matches("grey")
                assert_that(to_dateformat(remind.change_time)).is_equal_to(
                    "08-19-2024 21:00:00 +0300"
                )
                assert_that(to_dateformat(remind.remind_time)).is_equal_to(
                    "08-19-2024 20:45:00 +0300"
                )
