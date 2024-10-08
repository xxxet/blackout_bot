import logging
from datetime import datetime, timedelta
from enum import Enum
from math import floor

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    CommandHandler,
    Application,
    ContextTypes,
    CallbackQueryHandler,
    CallbackContext,
)

import config
from src.sql.models.subscription import Subscription
from src.sql.models.user import User
from src.sql.remind_obj import RemindObj
from src.sql.sql_service import SqlService
from src.sql.sql_time_finder import SqlTimeFinder

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class BotCommands(Enum):
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
    time_finders: dict[str, SqlTimeFinder] = {}

    def __init__(self, app: Application):
        self.app = app

    def _get_time_finder(self, group: str) -> SqlTimeFinder:
        if group not in self.time_finders:
            self.time_finders[group] = SqlTimeFinder(group, config.tz)
            self.time_finders[group].read_schedule()
        return self.time_finders[group]

    def _schedule_notification_job(
        self, user: User, group_name: str, hours_add: int = 0
    ) -> None:
        remind_obj = self._check_for_suppressed_notification(
            group_name,
            user.remind_before,
            datetime.now(tz=config.tz) + timedelta(hours=hours_add),
            suppress=user.suppress_night,
        )
        if remind_obj is None:
            remind_obj = self._get_time_finder(group_name).find_next_remind_time(
                notify_before=user.remind_before, hours_add=hours_add
            )
        self.app.job_queue.run_once(
            self._notification,
            name=str(user.tg_id),
            when=1 if remind_obj.notify_now else remind_obj.remind_time,
            data=remind_obj,
            chat_id=user.tg_id,
        )

    def _check_for_suppressed_notification(
        self, group: str, remind_before: int, next_run: datetime, suppress: bool
    ) -> RemindObj | None:

        now = datetime.now(config.tz)
        today_silent_start = now.replace(
            hour=config.SILENT_PERIOD_START, minute=0, second=0
        )
        tomorrow_silent_end = (now + timedelta(days=1)).replace(
            hour=config.SILENT_PERIOD_STOP, minute=0, second=0
        )

        if today_silent_start <= next_run <= tomorrow_silent_end and suppress:
            hours_remaining = floor((tomorrow_silent_end - now).seconds / 3600)
            next_remind = self._get_time_finder(group).find_next_remind_time(
                notify_before=remind_before, hours_add=hours_remaining
            )
            return next_remind

        if next_run >= tomorrow_silent_end and not suppress:
            next_remind = self._get_time_finder(group).find_next_remind_time(
                notify_before=remind_before
            )
            return next_remind

        return None

    async def _notification(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.chat_id
        user = SqlService.get_user(chat_id)
        remind_obj = context.job.data
        await context.bot.send_message(
            chat_id=chat_id,
            text=remind_obj.get_msg(),
        )
        self._schedule_notification_job(user, remind_obj.group, hours_add=1)

    async def subscribe_action(
        self, chat_id: int, group: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if SqlService.subscribe_user(chat_id, group):
            user = SqlService.get_user(chat_id)
            self._schedule_notification_job(user, group)
            await context.bot.send_message(
                text=f"You are subscribed to {group}", chat_id=chat_id
            )
        else:
            await context.bot.send_message(
                text=f"You are already subscribed to {group}", chat_id=chat_id
            )

    async def subscribe_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        groups = SqlService.get_all_groups()
        keyboard = [
            [
                InlineKeyboardButton(
                    grp.group_name,
                    callback_data=f"{BotCommands.SUBSCRIBE.value}_" + grp.group_name,
                )
            ]
            for grp in groups
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Choose group",
            reply_markup=reply_markup,
        )

    async def stop_command(
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

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        keyboard = [
            [
                InlineKeyboardButton(
                    "Stop all notifications", callback_data=BotCommands.STOP.value
                ),
                InlineKeyboardButton("Status", callback_data=BotCommands.STATUS.value),
            ],
            [
                InlineKeyboardButton(
                    "Subscribe to group", callback_data=BotCommands.SUBSCRIBE.value
                ),
                InlineKeyboardButton(
                    "Unsubscribe from group",
                    callback_data=BotCommands.UNSUBSCRIBE.value,
                ),
            ],
            [
                InlineKeyboardButton(
                    "Today schedule", callback_data=BotCommands.TODAY.value
                ),
                InlineKeyboardButton(
                    "Tomorrow schedule", callback_data=BotCommands.TOMORROW.value
                ),
            ],
            [
                InlineKeyboardButton("Config", callback_data=BotCommands.CONFIG.value),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Please choose:",
            reply_markup=reply_markup,
        )

    async def config_command(
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
                    callback_data=BotCommands.SUPPRESS.value,
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

    async def upd_notify_time_action(
        self, chat_id: int, notify_time: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"You will be reminded {notify_time} minutes before zone change",
        )
        subs = SqlService.get_subs_for_user(chat_id)
        await self._no_subscription_message(chat_id, subs, context)
        if len(subs) > 0:
            user = SqlService.update_user(tg_id=chat_id, remind_before=int(notify_time))
            for job in context.job_queue.get_jobs_by_name(str(chat_id)):
                job.schedule_removal()
            for sub in subs:
                self._schedule_notification_job(user, sub.group.group_name)

    async def suppress_notif_action(
        self, chat_id: int, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        user = SqlService.toggle_suppress_at_night(chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Suppress at night status is "
            f"{'enabled' if user.suppress_night else 'disabled'}",
        )
        jobs = context.job_queue.get_jobs_by_name(str(chat_id))

        for job in jobs:
            remind_obj = self._check_for_suppressed_notification(
                job.data.group,
                user.remind_before,
                job.job.next_run_time,
                suppress=user.suppress_night,
            )
            if remind_obj:
                job.schedule_removal()
                self.app.job_queue.run_once(
                    self._notification,
                    name=str(user.tg_id),
                    when=1 if remind_obj.notify_now else remind_obj.remind_time,
                    data=remind_obj,
                    chat_id=user.tg_id,
                )

    async def unsubscribe_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        subs = SqlService.get_subs_for_user(chat_id)
        keyboard = [
            [
                InlineKeyboardButton(
                    sub.group.group_name,
                    callback_data=f"{BotCommands.UNSUBSCRIBE.value}_"
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

    async def unsubscribe_action(
        self, chat_id: int, group: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        deleted_jobs = list(
            map(
                lambda job: job.schedule_removal(),
                filter(
                    lambda job: job.data.group == group,
                    context.job_queue.get_jobs_by_name(str(chat_id)),
                ),
            )
        )
        if len(deleted_jobs) > 0:
            await context.bot.send_message(
                chat_id=chat_id, text=f"Removed jobs: {len(deleted_jobs)}"
            )
        SqlService.delete_subs_for_user_group(chat_id, group)
        SqlService.delete_no_sub_user(chat_id)

    async def status_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        subs = SqlService.get_subs_for_user(chat_id)
        await self._no_subscription_message(chat_id, subs, context)
        for sub in subs:
            remind_obj = self._get_time_finder(
                sub.group.group_name
            ).find_next_remind_time(notify_before=sub.user.remind_before)
            await context.bot.send_message(
                chat_id=chat_id,
                text=remind_obj.get_msg(),
            )

    async def jobs_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = str(update.effective_user.id)
        jobs = context.job_queue.jobs()
        list_of_jobs = ""
        list_of_jobs += (
            f"Server time {datetime.now().strftime("%m-%d-%Y, %H:%M %Z")} \n"
        )
        list_of_jobs += f"Server time in EEST {datetime.now(config.tz).strftime("%m-%d-%Y, %H:%M %Z")} \n"
        for i, job in enumerate(jobs):
            list_of_jobs += (
                f"Job queue: {i} '{job.job.next_run_time.strftime("%m-%d-%Y, %H:%M %Z")}'"
                f" '{job.job.id}' "
                f" '{job.data}'\n\n"
            )
        await context.bot.send_message(text=f"{list_of_jobs}", chat_id=chat_id)

    async def _show_schedule_for_day(
        self, chat_id: int, day: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        subs = SqlService.get_subs_for_user(chat_id)
        await self._no_subscription_message(chat_id, subs, context)
        for sub in subs:
            schedule = SqlService.get_schedule_for(day, sub.group.group_name)
            await context.bot.send_message(
                chat_id=chat_id,
                text="\n".join(
                    [f"Schedule for {day} for {sub.group.group_name}:"] + schedule
                ),
            )

    async def today_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        today = datetime.now(config.tz).strftime("%A")
        await self._show_schedule_for_day(chat_id, today, context)

    async def tomorrow_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        tomorrow = (datetime.now(config.tz) + timedelta(days=1)).strftime("%A")
        await self._show_schedule_for_day(chat_id, tomorrow, context)

    async def _no_subscription_message(
        self, chat_id: int, subs: list[Subscription], context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if len(subs) == 0:
            await context.bot.send_message(
                chat_id=chat_id, text=f"You are not subscribed, {chat_id}"
            )

    async def keyboard_handler(self, update: Update, callback: CallbackContext) -> None:
        query = update.callback_query
        await query.answer(text=f"Selected option: {query.data}")
        match query.data.split("_"):
            case [BotCommands.CONFIG.value]:
                await self.config_command(update, callback)
            case [BotCommands.SUBSCRIBE.value]:
                await self.subscribe_command(update, callback)
            case [BotCommands.UNSUBSCRIBE.value]:
                await self.unsubscribe_command(update, callback)
            case [BotCommands.STOP.value]:
                await self.stop_command(update, callback)
            case [BotCommands.STATUS.value]:
                await self.status_command(update, callback)
            case [BotCommands.TODAY.value]:
                await self.today_command(update, callback)
            case [BotCommands.TOMORROW.value]:
                await self.tomorrow_command(update, callback)
            case [BotCommands.NOTIFY_TIME.value, time]:
                await self.upd_notify_time_action(
                    update.effective_user.id, time, callback
                )
            case [BotCommands.SUPPRESS.value]:
                await self.suppress_notif_action(update.effective_user.id, callback)
            case [BotCommands.SUBSCRIBE.value, group]:
                await self.subscribe_action(update.effective_user.id, group, callback)
            case [BotCommands.UNSUBSCRIBE.value, group]:
                await self.unsubscribe_action(update.effective_user.id, group, callback)

    def _show_help(self) -> None:
        users = SqlService.get_all_users()

        async def message_func(context: ContextTypes.DEFAULT_TYPE) -> None:
            await context.bot.send_message(
                chat_id=context.job.chat_id, text=context.job.data
            )

        for user in users:
            if user.show_help:
                self.app.job_queue.run_once(
                    message_func,
                    name=str(user.tg_id),
                    when=1,
                    data="The bot has been updated, to see help, try /start",
                    chat_id=user.tg_id,
                )
                SqlService.update_user(user.tg_id, show_help=False)

    def _create_jobs(self) -> None:
        subs = SqlService.get_all_subs()
        for sub in subs:
            self._schedule_notification_job(sub.user, sub.group.group_name)


def main(token: str) -> None:
    application = Application.builder().token(token).build()
    outage_bot = OutageBot(application)
    start_handler = CommandHandler("start", outage_bot.start_command)
    subscribe_handler = CommandHandler("subscribe", outage_bot.subscribe_command)
    unsubscribe_handler = CommandHandler("unsubscribe", outage_bot.unsubscribe_command)
    stop_handler = CommandHandler("stop", outage_bot.stop_command)
    status_handler = CommandHandler("status", outage_bot.status_command)
    today_handler = CommandHandler("today", outage_bot.today_command)
    tomorrow_handler = CommandHandler("tomorrow", outage_bot.tomorrow_command)
    jobs_handler = CommandHandler("jobs", outage_bot.jobs_command)
    application.add_handler(CallbackQueryHandler(outage_bot.keyboard_handler))
    application.add_handler(start_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(unsubscribe_handler)
    application.add_handler(status_handler)
    application.add_handler(jobs_handler)
    application.add_handler(stop_handler)
    application.add_handler(today_handler)
    application.add_handler(tomorrow_handler)
    outage_bot._create_jobs()
    outage_bot._show_help()
    application.run_polling()
