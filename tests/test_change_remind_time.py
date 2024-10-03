import pytest
from assertpy import assert_that, soft_assertions
from freezegun import freeze_time

from src.sql.remind_obj import RemindObj
from src.tg.outage_bot import OutageBot
from tests.conftest import get_mock_remind
from tests.mock_utils import MockContext


class TestChangeRemindTime:

    @pytest.mark.parametrize(
        "reminder_before,reminder_after,remind_time",
        [
            (
                get_mock_remind(
                    remind_time="08-19-2024 20:45:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=False,
                ),
                get_mock_remind(
                    remind_time="08-19-2024 20:40:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=True,
                ),
                20,
            ),
            (
                get_mock_remind(
                    remind_time="08-19-2024 20:45:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=False,
                ),
                get_mock_remind(
                    remind_time="08-19-2024 20:50:00 +0300",
                    change_time="08-19-2024 21:00:00 +0300",
                    now=False,
                ),
                10,
            ),
        ],
    )
    @freeze_time("08-19-2024 20:44:59 +0300")
    @pytest.mark.asyncio
    async def test_change_remind_time(
        self,
        chat_id: int,
        context: MockContext,
        group5_bot: OutageBot,
        reminder_before: RemindObj,
        reminder_after: RemindObj,
        remind_time: str,
    ) -> None:
        context.job_queue.run_once(
            group5_bot._notification,
            name=str(chat_id),
            when=reminder_before.remind_time,
            data=reminder_before,
            chat_id=chat_id,
        )

        await group5_bot.upd_notify_time_action(chat_id, str(remind_time), context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            remind_obj = running_jobs[0].data
            minutes_diff = int(
                (remind_obj.change_time - remind_obj.remind_time).seconds / 60
            )
            assert_that(minutes_diff).is_equal_to(remind_time)
