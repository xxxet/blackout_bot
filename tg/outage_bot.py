import logging
from datetime import datetime

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
    jobs = {}

    def __init__(self, group_table_path):
        self.tz = pytz.timezone('Europe/Kyiv')
        self.time_finder = TimeFinder(group_table_path, 'Europe/Kyiv')
        self.time_finder.read_schedule()
        self.notify_before = 15

    def _add_job(self, chat_id, job):
        self.jobs[chat_id] = job

    async def notification(self, context: ContextTypes.DEFAULT_TYPE):
        # Beep the person who called this alarm:
        await context.bot.send_message(chat_id=context.job.chat_id, text=context.job.data)
        remind_time, msg = self.time_finder.find_next_remind_time(time_delta=20)
        job = context.job_queue.run_once(self.notification, when=remind_time,
                                         data=msg, chat_id=context.job.chat_id)
        self._add_job(context.job.chat_id, job)

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.jobs:
            job = self.jobs.pop(chat_id)
            job.schedule_removal()
            await update.message.reply_text(f'Stopped reminder for chat id: {chat_id}')
        else:
            await update.message.reply_text(f'No job found for chat id: {chat_id}')

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        # Set the alarm:
        if chat_id not in self.jobs:
            remind_time, msg = self.time_finder.find_next_remind_time(notify_before=15)
            await update.message.reply_text(
                f'Thanks you subscription, next update: \n' + msg)
            job = context.job_queue.run_once(self.notification, when=remind_time,
                                             data=msg, chat_id=chat_id)
            self._add_job(chat_id, job)
        else:
            await update.message.reply_text(f'You are already subscribed, {chat_id}')

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.jobs:
            remind_time, msg = self.time_finder.find_next_remind_time(delta_before=15)
            await update.message.reply_text(
                f'You are subscribed, \n' + msg)
        else:
            await update.message.reply_text(f'You are not subscribed, {chat_id}')

    async def jobs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        if chat_id in self.jobs:
            await update.message.reply_text(f'You are subscribed, {chat_id}')
        else:
            await update.message.reply_text(f'You are not subscribed, {chat_id}')
        jobs = context.job_queue.jobs()
        list_of_jobs = ""
        list_of_jobs += f"Server time {datetime.now().strftime("%m-%d-%Y, %H:%M %Z")} \n"
        list_of_jobs += f"Server time in EEST {datetime.now(self.tz).strftime("%m-%d-%Y, %H:%M %Z")} \n"
        for job in jobs:
            list_of_jobs += (f"Job queue: '{job.job.next_run_time.strftime("%m-%d-%Y, %H:%M %Z")}' '{job.job.id}' "
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
