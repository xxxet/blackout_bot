import logging
from datetime import datetime, timedelta
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
from src.sql.remind_obj import RemindObj
from src.sql.sql_service import SqlService
from src.sql.sql_time_finder import SqlTimeFinder

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


class OutageBot:
    subscribe_comm: str = "subscribe"
    unsubscribe_comm: str = "unsubscribe"
    tomorrow_comm: str = "tomorrow"
    today_comm: str = "today"
    status_comm: str = "status"
    stop_comm: str = "stop"
    # before_time: int = 15
    config_comm: str = "config"
    notify_time_commm = "notify"
    suppress_comm = "suppress"
    time_finders: dict[str, SqlTimeFinder] = {}

    def get_time_finder(self, group: str) -> SqlTimeFinder:
        if group not in self.time_finders:
            self.time_finders[group] = SqlTimeFinder(group, config.tz)
            self.time_finders[group].read_schedule()
        return self.time_finders[group]

    async def notification(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.chat_id
        user = SqlService.get_user(chat_id)
        remind_obj = context.job.data
        await self.send_notif_message(chat_id, context, remind_obj)
        remind_obj = self.get_time_finder(remind_obj.group).find_next_remind_time(
            notify_before=user.remind_before, hours_add=1
        )
        context.job_queue.run_once(
            self.notification,
            name=str(chat_id),
            when=remind_obj.remind_time,
            data=remind_obj,
            chat_id=chat_id,
        )

    async def message(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.chat_id
        await context.bot.send_message(chat_id=chat_id, text=context.job.data)

    async def send_notif_message(
        self, chat_id: int, context: ContextTypes.DEFAULT_TYPE, remind_obj: RemindObj
    ) -> None:
        await context.bot.send_message(
            chat_id=chat_id,
            text=remind_obj.get_msg(),
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
                    "Stop all notifications", callback_data=self.stop_comm
                ),
                InlineKeyboardButton("Status", callback_data=self.status_comm),
            ],
            [
                InlineKeyboardButton(
                    "Subscribe to group", callback_data=self.subscribe_comm
                ),
                InlineKeyboardButton(
                    "Unsubscribe from group", callback_data=self.unsubscribe_comm
                ),
            ],
            [
                InlineKeyboardButton("Today schedule", callback_data=self.today_comm),
                InlineKeyboardButton(
                    "Tomorrow schedule", callback_data=self.tomorrow_comm
                ),
            ],
            [
                InlineKeyboardButton("Config", callback_data=self.config_comm),
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

        keyboard = [
            [
                InlineKeyboardButton(
                    "Don't notify 23:00-08:00", callback_data=self.suppress_comm
                )
            ],
            [
                InlineKeyboardButton(
                    "Notify before 5 minutes",
                    callback_data="notify_5",
                )
            ],
            [
                InlineKeyboardButton(
                    "Notify before 15 minutes",
                    callback_data="notify_15",
                )
            ],
            [
                InlineKeyboardButton(
                    "Notify before 20 minutes",
                    callback_data="notify_20",
                )
            ],
            [
                InlineKeyboardButton(
                    "Notify before 30 minutes",
                    callback_data="notify_30",
                )
            ],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(
            chat_id=update.effective_user.id,
            text="Config options",
            reply_markup=reply_markup,
        )

    async def subscribe_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        groups = SqlService.get_all_groups()
        keyboard = [
            [
                InlineKeyboardButton(
                    grp.group_name,
                    callback_data=f"{self.subscribe_comm}_" + grp.group_name,
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

    async def upd_notify_time_action(
        self, chat_id: int, notify_time: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        # +add flag to db
        # delete user jobs
        # create jobs with new notify time
        pass

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
            suppressed_interval, remind_obj = self.check_for_suppressed_notification(
                job.data.group,
                user.remind_before,
                job.job.next_run_time,
                suppress=user.suppress_night,
            )
            if suppressed_interval:
                if isinstance(remind_obj, RemindObj):
                    job.schedule_removal()
                    context.job_queue.run_once(
                        self.notification,
                        name=str(chat_id),
                        when=remind_obj.remind_time,
                        data=remind_obj,
                        chat_id=chat_id,
                    )

    def check_for_suppressed_notification(
        self, group: str, remind_before: int, next_run: datetime, suppress: bool
    ) -> tuple[bool, RemindObj] | tuple[bool, None]:

        now = datetime.now(config.tz)
        today_23 = now.replace(hour=23, minute=0, second=0)
        tomorrow_8 = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0)

        if today_23 <= next_run <= tomorrow_8 and suppress:
            hours_remaining = floor((tomorrow_8 - now).seconds / 3600)
            next_remind = self.get_time_finder(group).find_next_remind_time(
                notify_before=remind_before, hours_add=hours_remaining
            )
            return True, next_remind

        if next_run >= tomorrow_8 and not suppress:
            next_remind = self.get_time_finder(group).find_next_remind_time(
                notify_before=remind_before
            )
            return True, next_remind

        return False, None

    async def subscribe_action(
        self, chat_id: int, group: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if SqlService.subscribe_user(chat_id, group):
            user = SqlService.get_user(chat_id)
            remind_obj = self.get_time_finder(group).find_next_remind_time(
                notify_before=user.remind_before
            )

            if not remind_obj.notify_now:
                await self.send_notif_message(chat_id, context, remind_obj)

            context.job_queue.run_once(
                self.notification,
                name=str(chat_id),
                when=1 if remind_obj.notify_now else remind_obj.remind_time,
                data=remind_obj,
                chat_id=chat_id,
            )
            await context.bot.send_message(
                text=f"You are subscribed to {group}", chat_id=chat_id
            )
        else:
            await context.bot.send_message(
                text=f"You are already subscribed to {group}", chat_id=chat_id
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
                    callback_data=f"{self.unsubscribe_comm}_" + sub.group.group_name,
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
        await self.check_for_subscription(chat_id, subs, context)
        for sub in subs:
            remind_obj = self.get_time_finder(
                sub.group.group_name
            ).find_next_remind_time(notify_before=sub.user.remind_before)
            await self.send_notif_message(chat_id, context, remind_obj)

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

    async def __show_schedule_for_day(
        self, chat_id: int, day: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        subs = SqlService.get_subs_for_user(chat_id)
        await self.check_for_subscription(chat_id, subs, context)
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
        await self.__show_schedule_for_day(chat_id, today, context)

    async def tomorrow_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        tomorrow = (datetime.now(config.tz) + timedelta(days=1)).strftime("%A")
        await self.__show_schedule_for_day(chat_id, tomorrow, context)

    async def check_for_subscription(
        self, chat_id: int, subs: list[Subscription], context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if len(subs) == 0:
            await context.bot.send_message(
                chat_id=chat_id, text=f"You are not subscribed, {chat_id}"
            )

    async def button(self, update: Update, callback: CallbackContext) -> None:
        query = update.callback_query
        await query.answer(text=f"Selected option: {query.data}")
        match query.data.split("_"):
            case [self.config_comm]:
                await self.config_command(update, callback)
            case [self.subscribe_comm]:
                await self.subscribe_command(update, callback)
            case [self.unsubscribe_comm]:
                await self.unsubscribe_command(update, callback)
            case [self.stop_comm]:
                await self.stop_command(update, callback)
            case [self.status_comm]:
                await self.status_command(update, callback)
            case [self.today_comm]:
                await self.today_command(update, callback)
            case [self.tomorrow_comm]:
                await self.tomorrow_command(update, callback)
            case [self.notify_time_commm, time]:
                await self.upd_notify_time_action(
                    update.effective_user.id, time, callback
                )
            case [self.suppress_comm]:
                await self.suppress_notif_action(update.effective_user.id, callback)
            case [self.subscribe_comm, group]:
                await self.subscribe_action(update.effective_user.id, group, callback)
            case [self.unsubscribe_comm, group]:
                await self.unsubscribe_action(update.effective_user.id, group, callback)

    def show_help(self, app: Application) -> None:
        users = SqlService.get_all_users()
        for user in users:
            if user.show_help:
                app.job_queue.run_once(
                    self.message,
                    name=str(user.tg_id),
                    when=datetime.now(tz=config.tz) + timedelta(minutes=1),
                    data="The bot has been updated, to see help, try /start",
                    chat_id=user.tg_id,
                )
                SqlService.update_user(user.tg_id, show_help=False)

    def create_jobs(self, app: Application) -> None:
        subs = SqlService.get_all_subs()
        for sub in subs:
            suppressed_notification, remind_obj = (
                self.check_for_suppressed_notification(
                    sub.group.group_name,
                    sub.user.remind_before,
                    datetime.now(tz=config.tz),
                    suppress=sub.user.suppress_night,
                )
            )
            if not suppressed_notification:
                remind_obj = self.get_time_finder(
                    sub.group.group_name
                ).find_next_remind_time(notify_before=sub.user.remind_before)
            if isinstance(remind_obj, RemindObj):
                app.job_queue.run_once(
                    self.notification,
                    name=str(sub.user_tg_id),
                    when=1 if remind_obj.notify_now else remind_obj.remind_time,
                    data=remind_obj,
                    chat_id=sub.user_tg_id,
                )


def main(token: str) -> None:
    application = Application.builder().token(token).build()
    outage_bot = OutageBot()
    start_handler = CommandHandler("start", outage_bot.start_command)
    subscribe_handler = CommandHandler("subscribe", outage_bot.subscribe_command)
    unsubscribe = CommandHandler("unsubscribe", outage_bot.unsubscribe_command)
    stop = CommandHandler("stop", outage_bot.stop_command)
    status_command = CommandHandler("status", outage_bot.status_command)
    today = CommandHandler("today", outage_bot.today_command)
    tomorrow = CommandHandler("tomorrow", outage_bot.tomorrow_command)
    jobs_command = CommandHandler("jobs", outage_bot.jobs_command)
    application.add_handler(CallbackQueryHandler(outage_bot.button))
    application.add_handler(start_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(unsubscribe)
    application.add_handler(status_command)
    application.add_handler(jobs_command)
    application.add_handler(stop)
    application.add_handler(today)
    application.add_handler(tomorrow)
    outage_bot.create_jobs(application)
    outage_bot.show_help(application)
    application.run_polling()
