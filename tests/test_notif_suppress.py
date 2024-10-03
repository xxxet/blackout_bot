import pytest
from assertpy import soft_assertions, assert_that
from freezegun import freeze_time

from src.sql.remind_obj import RemindObj
from src.sql.sql_service import SqlService
from src.tg.outage_bot import OutageBot
from tests.conftest import to_datetime, GROUP_5

from tests.mock_utils import MockContext


class TestNotifSuppress:

    def get_remind_obj(self, change_time: str, remind_time: str) -> RemindObj:
        return RemindObj(
            group=GROUP_5,
            old_zone="white",
            new_zone="black",
            change_time=to_datetime(change_time),
            remind_time=to_datetime(remind_time),
            notify_now=False,
        )

    @pytest.mark.parametrize(
        "remind_before_time,remind_after_time",
        [
            (
                ("08-19-2024 22:59:59 +0300", "08-19-2024 22:50:59 +0300"),
                ("08-19-2024 22:59:59 +0300", "08-19-2024 22:50:59 +0300"),
            ),
            (
                ("08-19-2024 23:01:00 +0300", "08-19-2024 23:00:00 +0300"),
                ("08-20-2024 09:00:00 +0300", "08-20-2024 08:45:00 +0300"),
            ),
            (
                ("08-20-2024 07:59:59 +0300", "08-20-2024 07:59:59 +0300"),
                ("08-20-2024 09:00:00 +0300", "08-20-2024 08:45:00 +0300"),
            ),
            (
                ("08-20-2024 08:00:01 +0300", "08-20-2024 08:00:01 +0300"),
                ("08-20-2024 08:00:01 +0300", "08-20-2024 08:00:01 +0300"),
            ),
        ],
    )
    @freeze_time("08-19-2024 23:00:00 +0300")
    @pytest.mark.asyncio
    async def test_enable_suppress(
        self,
        chat_id: int,
        context: MockContext,
        group5_bot: OutageBot,
        remind_before_time: list,
        remind_after_time: list,
    ) -> None:
        reminder_before_obj = self.get_remind_obj(*remind_before_time)
        reminder_after_obj = self.get_remind_obj(*remind_after_time)
        SqlService.update_user(chat_id, suppress_night=False)
        context.job_queue.run_once(
            group5_bot._notification,
            name=str(chat_id),
            when=reminder_before_obj.remind_time,
            data=reminder_before_obj,
            chat_id=chat_id,
        )

        await group5_bot.suppress_notif_action(chat_id, context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            assert_that(running_jobs[0].data.__dict__).is_equal_to(
                reminder_after_obj.__dict__
            )

    # on disable suppress notifications after 08:00 tomorrow should be rescheduled
    @pytest.mark.parametrize(
        "reminder_before,reminder_after",
        [
            (
                ("08-19-2024 22:59:59 +0300", "08-19-2024 22:59:59 +0300"),
                ("08-19-2024 22:59:59 +0300", "08-19-2024 22:59:59 +0300"),
            ),
            (
                ("08-19-2024 23:00:00 +0300", "08-19-2024 23:00:00 +0300"),
                ("08-19-2024 23:00:00 +0300", "08-19-2024 23:00:00 +0300"),
            ),
            (
                ("08-20-2024 07:59:59 +0300", "08-20-2024 07:59:59 +0300"),
                ("08-20-2024 07:59:59 +0300", "08-20-2024 07:59:59 +0300"),
            ),
            (
                ("08-20-2024 08:00:00 +0300", "08-20-2024 08:00:00 +0300"),
                ("08-20-2024 00:00:00 +0300", "08-19-2024 23:45:00 +0300"),
            ),
        ],
    )
    @freeze_time("08-19-2024 23:00:00 +0300")
    @pytest.mark.asyncio
    async def test_disable_suppress(
        self,
        chat_id: int,
        context: MockContext,
        group5_bot: OutageBot,
        reminder_before: str,
        reminder_after: str,
    ) -> None:
        reminder_before_obj = self.get_remind_obj(*reminder_before)
        reminder_after_obj = self.get_remind_obj(*reminder_after)
        SqlService.update_user(chat_id, suppress_night=True)
        context.job_queue.run_once(
            group5_bot._notification,
            name=str(chat_id),
            when=reminder_before_obj.remind_time,
            data=reminder_before_obj,
            chat_id=chat_id,
        )

        await group5_bot.suppress_notif_action(chat_id, context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            assert_that(running_jobs[0].data.__dict__).is_equal_to(
                reminder_after_obj.__dict__
            )
