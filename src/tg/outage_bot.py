import logging
from datetime import datetime, timedelta
from enum import Enum

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    Application,
    ContextTypes,
    CallbackQueryHandler,
    CallbackContext,
)

import config
from src.sql.sql_service import SqlService
from src.tg.bot_actions import BotActions

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class KeyboardCommands(Enum):
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    TOMORROW = "tomorrow"
    TODAY = "today"
    STATUS = "status"
    STOP = "stop"
    CONFIG = "config"
    NOTIFY_TIME = "notify"
    SUPPRESS = "suppress"


class OutageBot:

    def __init__(self, app: Application):
        self.app = app
        self.actions = BotActions(app)

    async def subscribe_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        groups = SqlService.get_all_groups()
        grp_names = list(map(lambda grp: grp.group_name, groups))
        grp_names.sort()
        keyboard = [
            [
                InlineKeyboardButton(
                    grp_name,
                    callback_data=f"{KeyboardCommands.SUBSCRIBE.value}_{grp_name}",
                )
            ]
            for grp_name in grp_names
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Choose group",
            reply_markup=reply_markup,
        )

    async def stop_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        deleted_jobs = list(
            map(
                lambda job: job.schedule_removal(),
                context.job_queue.get_jobs_by_name(str(chat_id)),
            )
        )
        await context.bot.send_message(
            chat_id=chat_id, text=f"Removed jobs: {len(deleted_jobs)}"
        )
        SqlService.delete_user_with_subs(chat_id)
        await context.bot.send_message(
            chat_id=chat_id, text="Stopped notifications for all groups"
        )

    async def start_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Stop all notifications", callback_data=KeyboardCommands.STOP.value
                ),
                InlineKeyboardButton(
                    "Status", callback_data=KeyboardCommands.STATUS.value
                ),
            ],
            [
                InlineKeyboardButton(
                    "Subscribe to group", callback_data=KeyboardCommands.SUBSCRIBE.value
                ),
                InlineKeyboardButton(
                    "Unsubscribe from group",
                    callback_data=KeyboardCommands.UNSUBSCRIBE.value,
                ),
            ],
            [
                InlineKeyboardButton(
                    "Today schedule", callback_data=KeyboardCommands.TODAY.value
                ),
                InlineKeyboardButton(
                    "Tomorrow schedule", callback_data=KeyboardCommands.TOMORROW.value
                ),
            ],
            [
                InlineKeyboardButton(
                    "Config", callback_data=KeyboardCommands.CONFIG.value
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Please choose:",
            reply_markup=reply_markup,
        )

    async def config_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user = SqlService.get_user(update.effective_user.id)

        keyboard = [
            [
                InlineKeyboardButton(
                    f"Notify before {option} minutes",
                    callback_data=f"notify_{option}",
                )
            ]
            for option in config.NOTIFY_BEFORE_OPTIONS
        ]

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Toggle don't notify period in "
                    f"{config.SILENT_PERIOD_START}-{config.SILENT_PERIOD_STOP}",
                    callback_data=KeyboardCommands.SUPPRESS.value,
                )
            ]
        )

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text=(
                "Config options"
                if user is None
                else f"Current config:\n"
                f"remind before {user.remind_before} minutes\n"
                f"suppress is {user.suppress_night}"
            ),
            reply_markup=reply_markup,
        )

    async def unsubscribe_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        subs = SqlService.get_subs_for_user(chat_id)
        keyboard = [
            [
                InlineKeyboardButton(
                    sub.group.group_name,
                    callback_data=f"{KeyboardCommands.UNSUBSCRIBE.value}_"
                    + sub.group.group_name,
                )
            ]
            for sub in subs
        ]
        if len(subs) == 0:
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="You are not subscribed to any group",
            )
        else:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(
                chat_id=update.effective_user.id,
                text="Unsubscribe from",
                reply_markup=reply_markup,
            )

    async def status_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await self.actions.status_action(update, context)

    async def jobs_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        df = "%m-%d-%Y, %H:%M %Z"
        chat_id = str(update.effective_user.id)
        jobs = context.job_queue.jobs()
        list_of_jobs = ""
        list_of_jobs += f"Server time {datetime.now().strftime(df)} \n"
        list_of_jobs += f"Server time in EEST {datetime.now(config.tz).strftime(df)} \n"
        for i, job in enumerate(jobs):
            list_of_jobs += (
                f"Job queue: {i} '{job.job.next_run_time.strftime(df)}'"
                f" '{job.job.id}' "
                f" '{job.data}'\n\n"
            )
        await context.bot.send_message(text=f"{list_of_jobs}", chat_id=chat_id)

    async def today_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        day = datetime.now(config.tz).strftime("%A")
        await self.actions.get_schedule_for_day(chat_id, day, context, today=True)

    async def tomorrow_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        day = (datetime.now(config.tz) + timedelta(days=1)).strftime("%A")
        await self.actions.get_schedule_for_day(chat_id, day, context)

    async def keyboard_handler(self, update: Update, callback: CallbackContext) -> None:
        query = update.callback_query
        await query.answer(text=f"Selected option: {query.data}")
        match query.data.split("_"):
            case [KeyboardCommands.CONFIG.value]:
                await self.config_handler(update, callback)
            case [KeyboardCommands.SUBSCRIBE.value]:
                await self.subscribe_handler(update, callback)
            case [KeyboardCommands.UNSUBSCRIBE.value]:
                await self.unsubscribe_handler(update, callback)
            case [KeyboardCommands.STOP.value]:
                await self.stop_handler(update, callback)
            case [KeyboardCommands.STATUS.value]:
                await self.status_handler(update, callback)
            case [KeyboardCommands.TODAY.value]:
                await self.today_handler(update, callback)
            case [KeyboardCommands.TOMORROW.value]:
                await self.tomorrow_handler(update, callback)
            case [KeyboardCommands.NOTIFY_TIME.value, time]:
                await self.actions.upd_notify_time_action(
                    update.effective_user.id, time, callback
                )
            case [KeyboardCommands.SUPPRESS.value]:
                await self.actions.suppress_notif_action(
                    update.effective_user.id, callback
                )
            case [KeyboardCommands.SUBSCRIBE.value, group]:
                await self.actions.subscribe_action(
                    update.effective_user.id, group, callback
                )
            case [KeyboardCommands.UNSUBSCRIBE.value, group]:
                await self.actions.unsubscribe_action(
                    update.effective_user.id, group, callback
                )


def main(token: str) -> None:
    application = Application.builder().token(token).build()
    outage_bot = OutageBot(application)
    start_handler = CommandHandler("start", outage_bot.start_handler)
    subscribe_handler = CommandHandler("subscribe", outage_bot.subscribe_handler)
    unsubscribe_handler = CommandHandler("unsubscribe", outage_bot.unsubscribe_handler)
    stop_handler = CommandHandler("stop", outage_bot.stop_handler)
    status_handler = CommandHandler("status", outage_bot.status_handler)
    today_handler = CommandHandler("today", outage_bot.today_handler)
    tomorrow_handler = CommandHandler("tomorrow", outage_bot.tomorrow_handler)
    jobs_handler = CommandHandler("jobs", outage_bot.jobs_handler)
    application.add_handler(CallbackQueryHandler(outage_bot.keyboard_handler))
    application.add_handler(start_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(unsubscribe_handler)
    application.add_handler(status_handler)
    application.add_handler(jobs_handler)
    application.add_handler(stop_handler)
    application.add_handler(today_handler)
    application.add_handler(tomorrow_handler)
    outage_bot.actions.create_jobs()
    outage_bot.actions.show_help()
    application.run_polling()
