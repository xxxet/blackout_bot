import logging
from datetime import datetime, timedelta

import pytz
from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes

from tg.time_finder import TimeFinder

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OutageBot:

    def __init__(self, group_table_path):
        timezone_str = 'Europe/Kyiv'
        self.tz = pytz.timezone(timezone_str)
        self.time_finder = TimeFinder(group_table_path, timezone_str)
        self.time_finder.read_schedule()
        self.before_time = 15

    async def notification(self, context: ContextTypes.DEFAULT_TYPE):
        chat_id = context.job.chat_id
        await context.bot.send_message(chat_id=chat_id, text=context.job.data)
        remind_time, msg = self.time_finder.find_next_remind_time(notify_before=self.before_time,
                                                                  time_delta=self.before_time + 5)
        context.job_queue.run_once(self.notification, name=str(chat_id), when=remind_time,
                                   data=msg, chat_id=chat_id)

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if context.job_queue.get_jobs_by_name(str(chat_id)):
            list(map(lambda job: job.schedule_removal(), context.job_queue.get_jobs_by_name(str(chat_id))))
            await update.message.reply_text(f'Stopped reminder for chat id: {chat_id}')
        else:
            await update.message.reply_text(f'No job found for chat id: {chat_id}')

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if not context.job_queue.get_jobs_by_name(str(chat_id)):
            remind_time, msg = self.time_finder.find_next_remind_time(notify_before=self.before_time)
            await update.message.reply_text(f'Thanks for subscription, next update: \n {msg}')
            context.job_queue.run_once(self.notification, name=str(chat_id), when=remind_time,
                                       data=msg, chat_id=chat_id)
        else:
            await update.message.reply_text(f'You are already subscribed, {chat_id}')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if context.job_queue.get_jobs_by_name(str(chat_id)):
            _, msg = self.time_finder.find_next_remind_time(notify_before=self.before_time)
            await update.message.reply_text(f'You are subscribed, \n {msg}')
        else:
            await update.message.reply_text(f'You are not subscribed, {chat_id}')

    async def jobs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if context.job_queue.get_jobs_by_name(str(chat_id)):
            await update.message.reply_text(f'You are subscribed, {chat_id}')
        else:
            await update.message.reply_text(f'You are not subscribed, {chat_id}')
        jobs = context.job_queue.jobs()
        list_of_jobs = ""
        list_of_jobs += f"Server time {datetime.now().strftime("%m-%d-%Y, %H:%M %Z")} \n"
        list_of_jobs += f"Server time in EEST {datetime.now(self.tz).strftime("%m-%d-%Y, %H:%M %Z")} \n"
        for job in jobs:
            list_of_jobs += (f"Job queue: '{job.job.next_run_time.strftime("%m-%d-%Y, %H:%M %Z")}'"
                             f" '{job.job.id}' "
                             f"'{job.user_id}' '{job.chat_id}' "
                             f"'{job.name}' '{job.data}'\n")
        await update.message.reply_text(f'{list_of_jobs}')


def main(group_table_path, token):
    outage_bot = OutageBot(group_table_path)
    application = Application.builder().token(token).build()
    start_handler = CommandHandler('start', outage_bot.start_command)
    stop_handler = CommandHandler('stop', outage_bot.stop_command)
    status_command = CommandHandler('status', outage_bot.status_command)
    jobs_command = CommandHandler('jobs', outage_bot.jobs_command)
    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.add_handler(status_command)
    application.add_handler(jobs_command)
    application.run_polling()
