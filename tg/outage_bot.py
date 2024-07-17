import logging
from datetime import datetime

import pytz
from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes

import config
from sql.sql_service import SqlOperationsService
from tg.sql_time_finder import SqlTimeFinder

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OutageBot:

    def __init__(self):
        self.timezone_str = 'Europe/Kyiv'
        self.tz = pytz.timezone(self.timezone_str)
        self.before_time = 15
        self.time_finders: dict[str, SqlTimeFinder] = {}

    def get_time_finder(self, group) -> SqlTimeFinder:
        if group in self.time_finders.keys():
            return self.time_finders.get(group)
        else:
            tf = SqlTimeFinder(group, self.timezone_str)
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

    async def send_notif_message(self, chat_id, context, remind_obj):
        await context.bot.send_message(chat_id=chat_id, text=f"Change for {remind_obj.group}:\n{remind_obj.get_msg()}")

    async def unsubscribe(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.message.chat_id)
        group = " ".join(context.args)
        if group == "":
            await update.message.reply_text(f'unsubscribe command should be used with group name')
            return
        deleted_jobs = list(map(lambda job: job.schedule_removal(),
                                filter(lambda job: job.data.group == group,
                                       context.job_queue.get_jobs_by_name(str(chat_id)))))
        if len(deleted_jobs) > 0:
            await update.message.reply_text(f'Removed jobs: {len(deleted_jobs)}')
        SqlOperationsService.delete_subs_for_user_group(chat_id, group)
        SqlOperationsService.delete_no_sub_user(chat_id)

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.message.chat_id)
        deleted_jobs = list(map(lambda job: job.schedule_removal(), context.job_queue.get_jobs_by_name(str(chat_id))))
        await update.message.reply_text(f'Removed jobs: {len(deleted_jobs)}')
        SqlOperationsService.delete_user_with_subs(chat_id)
        await update.message.reply_text('Stopped notifications for all groups')

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f'Available commands:\n/start \n'
                                        f'/stop group_name \n'
                                        f'/subscribe group_name')

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.message.chat_id)
        group = " ".join(context.args)
        if group == "":
            await update.message.reply_text("Subscribe command should be used with group name")
            return
        if SqlOperationsService.subscribe_user(chat_id, group):
            remind_obj = self.get_time_finder(group).find_next_remind_time(notify_before=self.before_time)
            context.job_queue.run_once(self.notification, name=str(chat_id), when=remind_obj.remind_time,
                                       data=remind_obj, chat_id=chat_id)
            await update.message.reply_text(f"You are subscribed to {group}")
            self.send_notif_message(chat_id, context, remind_obj)
        else:
            await update.message.reply_text(f"No such group {group} added yet")

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.message.chat_id)
        subs = SqlOperationsService.get_subs_for_user(chat_id)
        if len(subs) == 0:
            await update.message.reply_text(f'You are not subscribed, {chat_id}')
        for sub in subs:
            remind_obj = self.get_time_finder(sub.group.group_name).find_next_remind_time(
                notify_before=self.before_time)
            await self.send_notif_message(chat_id, context, remind_obj)

    async def jobs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = str(update.message.chat_id)
        if context.job_queue.get_jobs_by_name(str(chat_id)):
            await update.message.reply_text(f'You are subscribed, {chat_id}')
        else:
            await update.message.reply_text(f'You are not subscribed, {chat_id}')
        jobs = context.job_queue.jobs()
        list_of_jobs = ""
        list_of_jobs += f"Server time {datetime.now().strftime("%m-%d-%Y, %H:%M %Z")} \n"
        list_of_jobs += f"Server time in EEST {datetime.now(self.tz).strftime("%m-%d-%Y, %H:%M %Z")} \n"
        for i, job in enumerate(jobs):
            list_of_jobs += (f"Job queue: {i} '{job.job.next_run_time.strftime("%m-%d-%Y, %H:%M %Z")}'"
                             f" '{job.job.id}' "
                             f"'{job.user_id}' '{job.chat_id}' "
                             f"'{job.name}' '{job.data}'\n\n")
        await update.message.reply_text(f'{list_of_jobs}')

    def create_jobs(self, app: Application):
        subs = SqlOperationsService.get_all_subs()
        for sub in subs:
            remind_obj = self.get_time_finder(sub.group.group_name).find_next_remind_time(
                notify_before=self.before_time)
            app.job_queue.run_once(self.notification, name=str(sub.user_tg_id), when=remind_obj.remind_time,
                                   data=remind_obj, chat_id=sub.user_tg_id)

    async def today_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass

    async def tomorrow_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        pass


def main(token):
    outage_bot = OutageBot()
    application = Application.builder().token(token).build()
    start_handler = CommandHandler('start', outage_bot.start_command)
    subscribe_handler = CommandHandler('subscribe', outage_bot.subscribe_command)
    unsubscribe = CommandHandler('unsubscribe', outage_bot.unsubscribe)
    stop = CommandHandler('stop', outage_bot.stop_command)
    status_command = CommandHandler('status', outage_bot.status_command)
    today = CommandHandler('today', outage_bot.today_command)
    tomorrow = CommandHandler('tomorrow', outage_bot.tomorrow_command)
    jobs_command = CommandHandler('jobs', outage_bot.jobs_command)
    application.add_handler(start_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(unsubscribe)
    application.add_handler(status_command)
    application.add_handler(jobs_command)
    application.add_handler(stop)
    application.add_handler(today)
    application.add_handler(tomorrow)
    outage_bot.create_jobs(application)
    application.run_polling()
