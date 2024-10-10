import pytest
from assertpy import assert_that, soft_assertions
from freezegun import freeze_time

from src.sql.sql_service import SqlService
from src.tg.outage_bot import OutageBot
from tests.conftest import GROUP_5, GROUP_4
from tests.mock_utils import MockContext, MockUpdate


class TestTimeFinder:

    @pytest.mark.asyncio
    async def test_subscribe(
        self, chat_id: int, group5_bot: OutageBot, context: MockContext
    ) -> None:
        SqlService.delete_subs_for_user_group(chat_id, GROUP_5)
        await group5_bot.subscribe_action(chat_id, GROUP_5, context)
        subs = SqlService.get_subs_for_user(chat_id)
        with soft_assertions():
            assert_that(subs).extracting("group").extracting("group_name").contains(
                GROUP_5
            )
            assert_that(context.bot.sent_messages).contains(
                {"chat_id": chat_id, "text": f"You are subscribed to {GROUP_5}"}
            )

    @pytest.mark.asyncio
    async def test_subscribe_again(
        self, chat_id: int, group5_bot: OutageBot, context: MockContext
    ) -> None:
        SqlService.subscribe_user(chat_id, GROUP_5)
        await group5_bot.subscribe_action(chat_id, GROUP_5, context)
        subs = SqlService.get_subs_for_user(chat_id)
        with soft_assertions():
            assert_that(subs).extracting("group").extracting("group_name").contains(
                GROUP_5
            )
            assert_that(context.bot.sent_messages).contains(
                {"chat_id": chat_id, "text": f"You are already subscribed to {GROUP_5}"}
            )

    @pytest.mark.asyncio
    async def test_unsubscribe(
        self, chat_id: int, group5_bot: OutageBot, context: MockContext
    ) -> None:
        SqlService.delete_subs_for_user_group(chat_id, GROUP_5)
        await group5_bot.unsubscribe_action(chat_id, GROUP_5, context)
        subs = SqlService.get_subs_for_user(chat_id)
        assert_that(subs).extracting("group").extracting("group_name").does_not_contain(
            GROUP_5
        )

    @pytest.mark.asyncio
    async def test_stop(
        self, chat_id: int, group5_bot: OutageBot, context: MockContext
    ) -> None:
        await group5_bot.subscribe_action(chat_id, GROUP_4, context)
        await group5_bot.stop_command(MockUpdate(chat_id), context)
        subs = SqlService.get_subs_for_user(chat_id)
        assert_that(subs).is_length(0)

    @freeze_time("08-19-2024 20:45:00 +0300")
    @pytest.mark.asyncio
    async def test_today(
        self, chat_id: int, group5_bot: OutageBot, context: MockContext
    ) -> None:
        await group5_bot.today_command(MockUpdate(chat_id), context)
        assert_that(context.bot.sent_messages).extracting("text").contains(
            f"Schedule for Monday for {GROUP_5}:\n🌚 00:00: black\n"
            "🌥 02:00: grey\n💡 05:00: white\n"
            "🌚 06:00: black\n🌥 09:00: grey\n"
            "💡 12:00: white\n🌚 15:00: black\n"
            "🌥 18:00: grey\n💡 21:00: white"
        )

    @freeze_time("08-19-2024 20:45:00 +0300")
    @pytest.mark.asyncio
    async def test_tomorrow(
        self, chat_id: int, group5_bot: OutageBot, context: MockContext
    ) -> None:
        await group5_bot.tomorrow_command(MockUpdate(chat_id), context)
        assert_that(context.bot.sent_messages).extracting("text").contains(
            f"Schedule for Tuesday for {GROUP_5}:\n"
            "🌚 00:00: black\n🌥 03:00: grey\n"
            "💡 06:00: white\n🌚 09:00: black\n"
            "🌥 12:00: grey\n💡 15:00: white\n"
            "🌚 18:00: black\n🌥 21:00: grey"
        )
