import pytest
from assertpy import assert_that
from freezegun import freeze_time

from src.sql.remind_obj import RemindObj
from src.tg.outage_bot import OutageBot
from tests.conftest import to_datetime

from tests.mock_utils import MockContext


class TestTimeFinder:

    @freeze_time("08-19-2024 20:45:00 +0300")
    @pytest.mark.asyncio
    async def test_notify_before_remind_time(
        self, chat_id: int, group5_bot: OutageBot, context: MockContext
    ) -> None:
        reminder = RemindObj(
            group="group5",
            old_zone="white",
            new_zone="black",
            change_time=to_datetime("08-19-2024 21:00:00 +0300"),
            remind_time=to_datetime("08-19-2024 20:45:00 +0300"),
            notify_now=False,
        )

        context.job_queue.run_once(
            group5_bot._notification,
            name=str(chat_id),
            when=reminder.remind_time,
            data=reminder,
            chat_id=chat_id,
        )
        await group5_bot._notification(context=context)
        expected_remind = RemindObj(
            group="group5",
            old_zone="white",
            new_zone="black",
            change_time=to_datetime("08-20-2024 00:00:00 +0300"),
            remind_time=to_datetime("08-19-2024 23:45:00 +0300"),
            notify_now=False,
        )
        assert_that(context.job.data.__dict__).is_equal_to(expected_remind.__dict__)
