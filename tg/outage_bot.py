import logging

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

    def __init__(self):
        self.tz = pytz.timezone('Europe/Kyiv')
        self.time_finder = TimeFinder("../group5.png", 'Europe/Kyiv')
        self.time_finder.read_schedule()

    def _add_job(self, chat_id, job):
        self.jobs[chat_id] = job

    async def notification(self, context: ContextTypes.DEFAULT_TYPE):
        # Beep the person who called this alarm:
        await context.bot.send_message(chat_id=context.job.chat_id, text=context.job.data)
        remind_time = self.find_next_remind_time()
        job = context.job_queue.run_once(self.notification, when=remind_time,
                                         data=context.job.data,
                                         chat_id=context.job.chat_id)
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
            remind_time, msg = self.time_finder.find_next_remind_time()
            await update.message.reply_text(
                f'Thanks you subscription, next update: \n' + msg)
            job = context.job_queue.run_once(self.notification, when=remind_time, data=msg, chat_id=chat_id)
            self._add_job(chat_id, job)
        else:
            await update.message.reply_text(f'You are already subscribed, {chat_id}')


if __name__ == '__main__':
    outageBot = OutageBot()
    application = Application.builder().token('968012733:AAF3HZPm6ZjlBMVLd9KllSW17Dg7nq0Z1tw').build()
    start_handler = CommandHandler('start', outageBot.start_command)
    stop_handler = CommandHandler('stop', outageBot.stop_command)
    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.run_polling()
