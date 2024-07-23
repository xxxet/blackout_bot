import logging
from datetime import datetime, timedelta

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CommandHandler, Application, ContextTypes, CallbackQueryHandler, CallbackContext

import config
from sql.sql_service import SqlService
from tg.sql_time_finder import SqlTimeFinder

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OutageBot:

    def __init__(self):
        self.subscribe = "subscribe"
        self.unsubscribe = "unsubscribe"
        self.tomorrow = "tomorrow"
        self.today = "today"
        self.status = "status"
        self.stop = "stop"
        self.before_time = 15
        self.time_finders: dict[str, SqlTimeFinder] = {}

    def get_time_finder(self, group) -> SqlTimeFinder:
        if group in self.time_finders.keys():
            return self.time_finders.get(group)

        tf = SqlTimeFinder(group, config.tz)
        tf.read_schedule()
        self.time_finders[group] = tf
        return self.time_finders[group]

    async def notification(self, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(context.job.chat_id)
        remind_obj = context.job.data
        await self.send_notif_message(chat_id, context, remind_obj)
        remind_obj = self.get_time_finder(remind_obj.group).find_next_remind_time(notify_before=self.before_time,
                                                                                  time_delta=self.before_time + 5)
        context.job_queue.run_once(self.notification, name=str(chat_id), when=remind_obj.remind_time,
                                   data=remind_obj, chat_id=chat_id)

    async def message(self, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(context.job.chat_id)
        await context.bot.send_message(chat_id=chat_id, text=context.job.data)

    async def send_notif_message(self, chat_id, context, remind_obj):
        await context.bot.send_message(chat_id=chat_id, text=f"Change for {remind_obj.group}:\n{remind_obj.get_msg()}")

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_user.id
        deleted_jobs = list(map(lambda job: job.schedule_removal(), context.job_queue.get_jobs_by_name(str(chat_id))))
        await context.bot.send_message(chat_id=chat_id, text=f'Removed jobs: {len(deleted_jobs)}')
        SqlService.delete_user_with_subs(chat_id)
        await context.bot.send_message(chat_id=chat_id, text='Stopped notifications for all groups')

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        keyboard = [
            [InlineKeyboardButton("Stop all notifications", callback_data=self.stop),
             InlineKeyboardButton("Status", callback_data=self.status)],
            [InlineKeyboardButton("Subscribe to group", callback_data=self.subscribe),
             InlineKeyboardButton("Unsubscribe from group", callback_data=self.unsubscribe)],
            [InlineKeyboardButton("Today schedule", callback_data=self.today),
             InlineKeyboardButton("Tomorrow schedule", callback_data=self.tomorrow)],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_user.id, text="Please choose:",
                                       reply_markup=reply_markup)

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        groups = SqlService.get_all_groups()
        keyboard = [
            [InlineKeyboardButton(grp.group_name, callback_data=f"{self.subscribe}_" + grp.group_name) for grp in
             groups]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await context.bot.send_message(chat_id=update.effective_user.id, text="Choose group", reply_markup=reply_markup)

    async def subscribe_action(self, chat_id: int, group: str, context: ContextTypes.DEFAULT_TYPE):
        if SqlService.subscribe_user(chat_id, group):
            remind_obj = self.get_time_finder(group).find_next_remind_time(notify_before=self.before_time)
            context.job_queue.run_once(self.notification, name=str(chat_id), when=remind_obj.remind_time,
                                       data=remind_obj, chat_id=chat_id)
            await context.bot.send_message(text=f"You are subscribed to {group}", chat_id=chat_id)
            await self.send_notif_message(chat_id, context, remind_obj)
        else:
            await context.bot.send_message(text=f"You are already subscribed to {group}", chat_id=chat_id)

    async def unsubscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_user.id
        subs = SqlService.get_subs_for_user(chat_id)
        keyboard = [
            [InlineKeyboardButton(sub.group.group_name, callback_data=f"{self.unsubscribe}_" + sub.group.group_name) for
             sub in
             subs]]
        if len(subs) == 0:
            await context.bot.send_message(chat_id=update.effective_user.id, text="You are not subscribed to any group")
        else:
            reply_markup = InlineKeyboardMarkup(keyboard)
            await context.bot.send_message(chat_id=update.effective_user.id, text="Unsubscribe from",
                                           reply_markup=reply_markup)

    async def unsubscribe_action(self, chat_id: int, group: str, context: ContextTypes.DEFAULT_TYPE):
        deleted_jobs = list(map(lambda job: job.schedule_removal(),
                                filter(lambda job: job.data.group == group,
                                       context.job_queue.get_jobs_by_name(str(chat_id)))))
        if len(deleted_jobs) > 0:
            await context.bot.send_message(chat_id=chat_id, text=f'Removed jobs: {len(deleted_jobs)}')
        SqlService.delete_subs_for_user_group(chat_id, group)
        SqlService.delete_no_sub_user(chat_id)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_user.id
        subs = SqlService.get_subs_for_user(chat_id)
        await self.check_for_subscription(chat_id, subs, context)
        for sub in subs:
            remind_obj = self.get_time_finder(sub.group.group_name).find_next_remind_time(
                notify_before=self.before_time)
            await self.send_notif_message(chat_id, context, remind_obj)

    async def jobs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.effective_user.id)
        jobs = context.job_queue.jobs()
        list_of_jobs = ""
        list_of_jobs += f"Server time {datetime.now().strftime("%m-%d-%Y, %H:%M %Z")} \n"
        list_of_jobs += f"Server time in EEST {datetime.now(config.tz).strftime("%m-%d-%Y, %H:%M %Z")} \n"
        for i, job in enumerate(jobs):
            list_of_jobs += (f"Job queue: {i} '{job.job.next_run_time.strftime("%m-%d-%Y, %H:%M %Z")}'"
                             f" '{job.job.id}' "
                             f"'{job.user_id}' '{job.chat_id}' "
                             f"'{job.name}' '{job.data}'\n\n")
        await context.bot.send_message(text=f'{list_of_jobs}', chat_id=chat_id)

    async def __show_schedule_for_day(self, chat_id: int, day: str, context: ContextTypes.DEFAULT_TYPE):
        subs = SqlService.get_subs_for_user(chat_id)
        await self.check_for_subscription(chat_id, subs, context)
        for sub in subs:
            schedule = SqlService.get_schedule_for(day, sub.group.group_name)
            await context.bot.send_message(chat_id=chat_id, text="\n".join(
                [f"Schedule for {day} for {sub.group.group_name}:"] + schedule))

    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_user.id
        today = datetime.now(config.tz).strftime("%A")
        await self.__show_schedule_for_day(chat_id, today, context)

    async def tomorrow_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_user.id
        tomorrow = (datetime.now(config.tz) + timedelta(days=1)).strftime("%A")
        await self.__show_schedule_for_day(chat_id, tomorrow, context)

    async def check_for_subscription(self, chat_id, subs, context: ContextTypes.DEFAULT_TYPE):
        if len(subs) == 0:
            await context.bot.send_message(chat_id=chat_id, text=f'You are not subscribed, {chat_id}')

    async def button(self, update: Update, callback: CallbackContext) -> None:
        query = update.callback_query
        await query.answer(text=f"Selected option: {query.data}")
        match query.data.split("_"):
            case [self.subscribe]:
                await self.subscribe_command(update, callback)
            case [self.unsubscribe]:
                await self.unsubscribe_command(update, callback)
            case [self.stop]:
                await self.stop_command(update, callback)
            case [self.status]:
                await self.status_command(update, callback)
            case [self.today]:
                await self.today_command(update, callback)
            case [self.tomorrow]:
                await self.tomorrow_command(update, callback)
            case [self.subscribe, group]:
                await self.subscribe_action(update.effective_user.id, group, callback)
            case [self.unsubscribe, group]:
                await self.unsubscribe_action(update.effective_user.id, group, callback)

    def show_help(self, app: Application):
        users = SqlService.get_all_users()
        for user in users:
            if user.show_help:
                app.job_queue.run_once(self.message, name=str(user.tg_id),
                                       when=datetime.now(tz=config.tz) + timedelta(minutes=1),
                                       data="The bot has been updated, to see help, try /start", chat_id=user.tg_id)
                SqlService.update_user_help(user.tg_id, False)

    def create_jobs(self, app: Application):
        subs = SqlService.get_all_subs()
        for sub in subs:
            remind_obj = self.get_time_finder(sub.group.group_name).find_next_remind_time(
                notify_before=self.before_time)
            app.job_queue.run_once(self.notification, name=str(sub.user_tg_id),
                                   when=remind_obj.remind_time + timedelta(minutes=1),
                                   data=remind_obj, chat_id=sub.user_tg_id)


def main(token):
    application = Application.builder().token(token).build()
    outage_bot = OutageBot()
    start_handler = CommandHandler('start', outage_bot.start_command)
    subscribe_handler = CommandHandler('subscribe', outage_bot.subscribe_command)
    unsubscribe = CommandHandler('unsubscribe', outage_bot.unsubscribe_command)
    stop = CommandHandler('stop', outage_bot.stop_command)
    status_command = CommandHandler('status', outage_bot.status_command)
    today = CommandHandler('today', outage_bot.today_command)
    tomorrow = CommandHandler('tomorrow', outage_bot.tomorrow_command)
    jobs_command = CommandHandler('jobs', outage_bot.jobs_command)
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
