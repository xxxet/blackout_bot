import pytest
from assertpy import assert_that, soft_assertions
from freezegun import freeze_time

from src.sql.remind_obj import RemindObj
from src.tg.outage_bot import OutageBot
from tests import in_dateformat
from tests.mock_utils import MockContext


def get_remind_obj(change_time: str, remind_time: str, now: bool = False) -> RemindObj:
    return RemindObj(
        group="group5",
        old_zone="grey",
        new_zone="white",
        change_time=in_dateformat(change_time),
        remind_time=in_dateformat(remind_time),
        notify_now=now,
    )


class TestChangeRemindTime:

    @pytest.mark.parametrize(
        "reminder_before,reminder_after,remind_time",
        [
            (
                get_remind_obj(
                    remind_time="08-19-2024 20:45:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=False,
                ),
                get_remind_obj(
                    remind_time="08-19-2024 20:40:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=True,
                ),
                "20",
            ),
            (
                get_remind_obj(
                    remind_time="08-19-2024 20:45:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=False,
                ),
                get_remind_obj(
                    remind_time="08-19-2024 20:50:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=False,
                ),
                "10",
            ),
        ],
    )
    @freeze_time("08-19-2024 20:44:59 +0300")
    @pytest.mark.asyncio
    async def test_change_remind_time(
        self,
        chat_id: int,
        context: MockContext,
        test_bot: OutageBot,
        reminder_before: RemindObj,
        reminder_after: RemindObj,
        remind_time: str,
    ) -> None:
        context.job_queue.run_once(
            test_bot._notification,
            name=str(chat_id),
            when=reminder_before.remind_time,
            data=reminder_before,
            chat_id=chat_id,
        )

        await test_bot.upd_notify_time_action(chat_id, remind_time, context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            remind = running_jobs[0].data
            assert_that(remind.notify_now).is_equal_to(reminder_after.notify_now)
            assert_that(remind.remind_time).is_equal_to(reminder_after.remind_time)
            assert_that(remind.change_time).is_equal_to(reminder_after.change_time)
