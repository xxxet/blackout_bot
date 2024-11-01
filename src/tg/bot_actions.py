import logging
from datetime import datetime, timedelta
from math import floor

from telegram import Update
from telegram.ext import (
    Application,
    ContextTypes,
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


class BotActions:
    time_finders: dict[str, SqlTimeFinder] = {}

    def __init__(self, app: Application):
        self.app = app

    async def subscribe_action(
        self, chat_id: int, group: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if SqlService.subscribe_user(chat_id, group):
            user = SqlService.get_user(chat_id)
            self.schedule_notification_job(user, group)
            await context.bot.send_message(
                text=f"You are subscribed to {group}", chat_id=chat_id
            )
        else:
            await context.bot.send_message(
                text=f"You are already subscribed to {group}", chat_id=chat_id
            )

    async def upd_notify_time_action(
        self, chat_id: int, notify_time: str, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"You will be reminded {notify_time} minutes before zone change",
        )
        subs = SqlService.get_subs_for_user(chat_id)
        await self.no_subscription_message(chat_id, subs, context)
        if len(subs) > 0:
            user = SqlService.update_user(tg_id=chat_id, remind_before=int(notify_time))
            for job in context.job_queue.get_jobs_by_name(str(chat_id)):
                job.schedule_removal()
            for sub in subs:
                self.schedule_notification_job(user, sub.group.group_name)

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

    def get_time_finder(self, group: str) -> SqlTimeFinder:
        if group not in self.time_finders:
            self.time_finders[group] = SqlTimeFinder(group, config.tz)
            self.time_finders[group].read_schedule()
        return self.time_finders[group]

    def schedule_notification_job(
        self, user: User, group_name: str, hours_add: int = 0
    ) -> None:
        remind_obj = self._check_for_suppressed_notification(
            group_name,
            user.remind_before,
            datetime.now(tz=config.tz) + timedelta(hours=hours_add),
            suppress=user.suppress_night,
        )
        if remind_obj is None:
            remind_obj = self.get_time_finder(group_name).find_next_remind_time(
                notify_before=user.remind_before, hours_add=hours_add
            )
        self.app.job_queue.run_once(
            self._notification,
            name=str(user.tg_id),
            when=1 if remind_obj.notify_now else remind_obj.remind_time,
            data=remind_obj,
            chat_id=user.tg_id,
        )

    async def no_subscription_message(
        self, chat_id: int, subs: list[Subscription], context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        if len(subs) == 0:
            await context.bot.send_message(
                chat_id=chat_id, text=f"You are not subscribed, {chat_id}"
            )

    async def _notification(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        chat_id = context.job.chat_id
        user = SqlService.get_user(chat_id)
        remind_obj = context.job.data
        await context.bot.send_message(
            chat_id=chat_id,
            text=remind_obj.get_msg(),
        )
        self.schedule_notification_job(user, remind_obj.group, hours_add=1)

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
            next_remind = self.get_time_finder(group).find_next_remind_time(
                notify_before=remind_before, hours_add=hours_remaining
            )
            return next_remind

        if next_run >= tomorrow_silent_end and not suppress:
            next_remind = self.get_time_finder(group).find_next_remind_time(
                notify_before=remind_before
            )
            return next_remind

        return None

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

    async def get_schedule_for_day(
        self,
        chat_id: int,
        day: str,
        context: ContextTypes.DEFAULT_TYPE,
        today: bool = False,
    ) -> None:
        cur_date = datetime.now(tz=config.tz)

        def fancy_schedule(raw_schedule: list, zone_arrow: bool) -> list[str]:
            cur_zone_found = False
            cur_hour = cur_date.hour
            res = []
            for row in raw_schedule:
                line = ""
                if cur_hour < row.hour and zone_arrow and not cur_zone_found:
                    line += "→"
                    cur_zone_found = True
                line += (
                    f"{RemindObj.symbol(row.zone_name)} {row.hour}:00 {row.zone_name}"
                )
                res.append(line)
            return res

        subs = SqlService.get_subs_for_user(chat_id)
        await self.no_subscription_message(chat_id, subs, context)
        for sub in subs:
            schedule = fancy_schedule(
                SqlService.get_schedule_for(day, sub.group.group_name), today
            )
            await context.bot.send_message(
                chat_id=chat_id,
                text="\n".join(
                    [f"Schedule for {day} for {sub.group.group_name}:"] + schedule
                ),
            )

    async def status_action(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        chat_id = update.effective_user.id
        subs = SqlService.get_subs_for_user(chat_id)
        await self.no_subscription_message(chat_id, subs, context)
        for sub in subs:
            remind_obj = self.get_time_finder(
                sub.group.group_name
            ).find_next_remind_time(notify_before=sub.user.remind_before)
            await context.bot.send_message(
                chat_id=chat_id,
                text=remind_obj.get_msg(),
            )

    def get_jobs(self) -> list[str]:
        df = "%m-%d-%Y, %H:%M %Z"
        jobs = self.app.job_queue.jobs()
        header = (
            f"Server time {datetime.now().strftime(df)} \n"
            f"Server time in EEST {datetime.now(config.tz).strftime(df)} \n"
        )

        ex_jobs = [
            f"Job queue: {i} '{job.job.next_run_time.strftime(df)}'"
            f" '{job.job.id}' "
            f" '{job.data}'\n\n"
            for i, job in enumerate(jobs)
        ]
        return [header] + ex_jobs

    def show_help(self) -> None:
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

    def create_jobs(self) -> None:
        subs = SqlService.get_all_subs()
        for sub in subs:
            self.schedule_notification_job(sub.user, sub.group.group_name)
