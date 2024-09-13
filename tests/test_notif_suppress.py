from datetime import datetime

import pytest
from assertpy import soft_assertions, assert_that
from freezegun import freeze_time

import src.tg.outage_bot as outage
from src.sql.remind_obj import RemindObj
from src.sql.sql_service import SqlService
from src.tg.outage_bot import OutageBot
from tests.mock_utils import MockContext, MockBot

d_format = "%Y-%m-%d %H:%M:%S %z"


class TestOutageBot:

    @pytest.fixture
    def bot(self) -> OutageBot:
        return outage.OutageBot()

    @pytest.fixture
    def chat_id(self) -> int:
        return 197188045

    @pytest.fixture
    def context(self) -> MockContext:
        return MockContext(MockBot())

    def get_remind_obj(self, change_time: str, remind_time: str) -> RemindObj:
        return RemindObj(
            group="group5",
            old_zone="white",
            new_zone="black",
            change_time=datetime.strptime(change_time, d_format),
            remind_time=datetime.strptime(remind_time, d_format),
            notify_now=False,
        )

    @pytest.mark.parametrize(
        "reminder_before,reminder_after",
        [
            (
                ("2024-08-19 22:59:59 +0300", "2024-08-19 22:50:59 +0300"),
                ("2024-08-19 22:59:59 +0300", "2024-08-19 22:50:59 +0300"),
            ),
            (
                ("2024-08-19 23:01:00 +0300", "2024-08-19 23:00:00 +0300"),
                ("2024-08-20 09:00:00 +0300", "2024-08-20 08:45:00 +0300"),
            ),
            (
                ("2024-08-20 07:59:59 +0300", "2024-08-20 07:59:59 +0300"),
                ("2024-08-20 09:00:00 +0300", "2024-08-20 08:45:00 +0300"),
            ),
            (
                ("2024-08-20 08:00:01 +0300", "2024-08-20 08:00:01 +0300"),
                ("2024-08-20 08:00:01 +0300", "2024-08-20 08:00:01 +0300"),
            ),
        ],
    )
    @freeze_time("2024-08-19 22:00:00", tz_offset=-3)
    @pytest.mark.asyncio
    async def test_enable_suppress(
        self,
        bot: OutageBot,
        chat_id: int,
        context: MockContext,
        reminder_before: str,
        reminder_after: str,
    ) -> None:
        reminder_before_obj = self.get_remind_obj(*reminder_before)
        reminder_after_obj = self.get_remind_obj(*reminder_after)

        SqlService.update_user(chat_id, suppress_night=False)
        context.job_queue.run_once(
            bot.notification,
            name=str(chat_id),
            when=reminder_before_obj.remind_time,
            data=reminder_before_obj,
            chat_id=chat_id,
        )

        await bot.suppress_notif_action(chat_id, context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            assert_that(repr(running_jobs[0].data)).is_equal_to(
                repr(reminder_after_obj)
            )

    @pytest.mark.parametrize(
        "reminder_before,reminder_after",
        [
            (
                ("2024-08-19 22:59:59 +0300", "2024-08-19 22:59:59 +0300"),
                ("2024-08-19 22:59:59 +0300", "2024-08-19 22:59:59 +0300"),
            ),
            (
                ("2024-08-19 23:00:00 +0300", "2024-08-19 23:00:00 +0300"),
                ("2024-08-19 23:00:00 +0300", "2024-08-19 23:00:00 +0300"),
            ),
            (
                ("2024-08-20 07:59:59 +0300", "2024-08-20 07:59:59 +0300"),
                ("2024-08-20 07:59:59 +0300", "2024-08-20 07:59:59 +0300"),
            ),
            (
                ("2024-08-20 08:00:00 +0300", "2024-08-20 08:00:00 +0300"),
                ("2024-08-20 00:00:00 +0300", "2024-08-19 23:45:00 +0300"),
            ),
        ],
    )
    @freeze_time("2024-08-19 22:00:00", tz_offset=-3)
    @pytest.mark.asyncio
    async def test_disable_suppress(
        self,
        bot: OutageBot,
        chat_id: int,
        context: MockContext,
        reminder_before: str,
        reminder_after: str,
    ) -> None:
        reminder_before_obj = self.get_remind_obj(*reminder_before)
        reminder_after_obj = self.get_remind_obj(*reminder_after)

        SqlService.update_user(chat_id, suppress_night=True)
        context.job_queue.run_once(
            bot.notification,
            name=str(chat_id),
            when=reminder_before_obj.remind_time,
            data=reminder_before_obj,
            chat_id=chat_id,
        )

        await bot.suppress_notif_action(chat_id, context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            assert_that(repr(running_jobs[0].data)).is_equal_to(
                repr(reminder_after_obj)
            )
