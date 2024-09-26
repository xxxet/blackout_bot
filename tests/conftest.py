import pytest

from src.sql.sql_service import SqlService
from src.tg.outage_bot import OutageBot
from tests.mock_utils import MockContext, MockApplication, MockBot


@pytest.fixture
def chat_id() -> int:
    return 12345


@pytest.fixture
def context() -> MockContext:
    return MockContext(MockBot())


@pytest.fixture
def test_bot(chat_id: int, context: MockContext) -> OutageBot:
    bot = OutageBot(MockApplication(context))
    SqlService.update_user(chat_id, suppress_night=False, remind_before=15)
    SqlService.subscribe_user(chat_id, "group5")
    return bot
