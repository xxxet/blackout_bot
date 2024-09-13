from assertpy import assert_that, soft_assertions
from freezegun import freeze_time

import config
from src.sql.sql_time_finder import SqlTimeFinder

date_format = "%m-%d-%Y, %H:%M %Z"


class TestTimeFinder:

    @freeze_time("2024-08-19 20:44:59", tz_offset=-3)
    def test_notify_before_remind_time(self) -> None:
        """Test notification before 'notify before time'"""
        tf = SqlTimeFinder("group5", config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15)
        with soft_assertions():
            assert_that(remind.notify_now).is_equal_to(False)
            assert_that(remind.new_zone).matches("white")
            assert_that(remind.old_zone).matches("grey")
            assert_that(remind.change_time.strftime("%m-%d-%Y, %H:%M %Z")).matches(
                "08-19-2024, 21:00 EEST"
            )
            assert_that(remind.remind_time.strftime("%m-%d-%Y, %H:%M %Z")).matches(
                "08-19-2024, 20:45 EEST"
            )

    @freeze_time("2024-08-19 20:45:00", tz_offset=-3)
    def test_notify_after_remind_time(self) -> None:
        """Test notification in 'notify before time'"""
        tf = SqlTimeFinder("group5", config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15)
        with soft_assertions():
            assert_that(remind.notify_now).is_equal_to(True)
            assert_that(remind.new_zone).matches("white")
            assert_that(remind.old_zone).matches("grey")
            assert_that(remind.change_time.strftime("%m-%d-%Y, %H:%M %Z")).matches(
                "08-19-2024, 21:00 EEST"
            )
            assert_that(remind.remind_time.strftime("%m-%d-%Y, %H:%M %Z")).matches(
                "08-19-2024, 20:45 EEST"
            )

    @freeze_time("2024-08-19 20:45:00", tz_offset=-3)
    def test_notify_in_next_hour(self) -> None:
        """Test notification for next hour"""
        tf = SqlTimeFinder("group5", config.tz)
        tf.read_schedule()
        remind = tf.find_next_remind_time(15, hours_add=1)
        with soft_assertions():
            assert_that(remind.notify_now).is_equal_to(False)
            assert_that(remind.new_zone).matches("black")
            assert_that(remind.old_zone).matches("white")
            assert_that(remind.change_time.strftime("%m-%d-%Y, %H:%M %Z")).matches(
                "08-20-2024, 00:00 EEST"
            )
            assert_that(remind.remind_time.strftime("%m-%d-%Y, %H:%M %Z")).matches(
                "08-19-2024, 23:45 EEST"
            )
