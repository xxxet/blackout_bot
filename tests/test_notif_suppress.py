from datetime import datetime

import pytest
from assertpy import soft_assertions, assert_that
from freezegun import freeze_time

import src.tg.outage_bot as outage
from src.sql.remind_obj import RemindObj
from src.sql.sql_service import SqlService
from tests.mock_utils import MockContext, MockBot, MockApplication

d_format = "%Y-%m-%d %H:%M:%S %z"


class TestOutageBot:

    @pytest.fixture
    def chat_id(self) -> int:
        return 12345

    @pytest.fixture
    def context(self) -> MockContext:
        return MockContext(MockBot())

    @pytest.fixture(autouse=True)
    def bot(self, context: MockContext) -> None:
        self.bot = outage.OutageBot(MockApplication(context))

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
    @freeze_time("2024-08-19 20:00:00")
    @pytest.mark.asyncio
    async def test_enable_suppress(
        self,
        chat_id: int,
        context: MockContext,
        reminder_before: str,
        reminder_after: str,
    ) -> None:
        reminder_before_obj = self.get_remind_obj(*reminder_before)
        reminder_after_obj = self.get_remind_obj(*reminder_after)

        SqlService.update_user(chat_id, suppress_night=False)
        context.job_queue.run_once(
            self.bot.notification,
            name=str(chat_id),
            when=reminder_before_obj.remind_time,
            data=reminder_before_obj,
            chat_id=chat_id,
        )

        await self.bot.suppress_notif_action(chat_id, context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            assert_that(repr(running_jobs[0].data)).is_equal_to(
                repr(reminder_after_obj)
            )

    # on disable suppress notifications after 08:00 tomorrow should be rescheduled
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
    @freeze_time("2024-08-19 20:00:00")
    @pytest.mark.asyncio
    async def test_disable_suppress(
        self,
        chat_id: int,
        context: MockContext,
        reminder_before: str,
        reminder_after: str,
    ) -> None:
        reminder_before_obj = self.get_remind_obj(*reminder_before)
        reminder_after_obj = self.get_remind_obj(*reminder_after)

        SqlService.update_user(chat_id, suppress_night=True)
        context.job_queue.run_once(
            self.bot.notification,
            name=str(chat_id),
            when=reminder_before_obj.remind_time,
            data=reminder_before_obj,
            chat_id=chat_id,
        )

        await self.bot.suppress_notif_action(chat_id, context)

        running_jobs = [job for job in context.job_queue.jobs if job.removed is False]
        with soft_assertions():
            assert_that(running_jobs).is_length(1)
            assert_that(repr(running_jobs[0].data)).is_equal_to(
                repr(reminder_after_obj)
            )
