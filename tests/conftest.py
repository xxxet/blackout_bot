from datetime import datetime

import pytest

from src.sql.remind_obj import RemindObj
from src.sql.sql_service import SqlService
from src.tg.outage_bot import OutageBot
from tests.mock_utils import MockContext, MockApplication, MockBot

DATE_FORMAT = "%m-%d-%Y %H:%M:%S %z"
GROUP_5 = "group5"


@pytest.fixture
def chat_id() -> int:
    return 12345


@pytest.fixture
def context() -> MockContext:
    return MockContext(MockBot())


@pytest.fixture
def group5_bot(chat_id: int, context: MockContext) -> OutageBot:
    bot = OutageBot(MockApplication(context))
    SqlService.update_user(chat_id, suppress_night=False, remind_before=15)
    SqlService.subscribe_user(chat_id, GROUP_5)
    return bot


def to_datetime(date_string: str) -> datetime:
    return datetime.strptime(date_string, DATE_FORMAT)


def to_dateformat(date_obj: datetime) -> str:
    return date_obj.strftime(DATE_FORMAT)


def get_mock_remind(change_time: str, remind_time: str, now: bool = False) -> RemindObj:
    return RemindObj(
        group="mock_group",
        old_zone="old_zone",
        new_zone="new_zone",
        change_time=to_datetime(change_time),
        remind_time=to_datetime(remind_time),
        notify_now=now,
    )
