import logging
from datetime import datetime
from datetime import timedelta

import pytz
from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


class OutageBot:
    jobs = {}

    def __init__(self):
        self.tz = pytz.timezone('Europe/Kyiv')

    def _add_job(self, chat_id, job):
        self.jobs[chat_id] = job

    async def notification(self, context: ContextTypes.DEFAULT_TYPE):
        # Beep the person who called this alarm:
        await context.bot.send_message(chat_id=context.job.chat_id, text=f'BEEP {context.job.data}!')
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
        name = update.effective_chat.full_name
        # Set the alarm:
        if chat_id not in self.jobs:
            remind_time = self.find_next_remind_time()
            await update.message.reply_text(
                f'Thanks you subscription {chat_id}, next update: ' + remind_time.strftime("%H:%M:%S"))
            logger.info(f"next notification time: {remind_time.strftime("%H:%M:%S")}")
            job = context.job_queue.run_once(self.notification, when=remind_time, data=name, chat_id=chat_id)
            self._add_job(chat_id, job)
        else:
            await update.message.reply_text(f'You are already subscribed {chat_id}')

    def find_next_remind_time(self):
        now = datetime.now(self.tz)
        time_change = timedelta(minutes=1)
        new_time = now + time_change
        if new_time.second <= 55:
            return new_time.replace(second=55)
        return new_time


# when callback triggered:
# find the next time zone change, set reminder on this time

# create callback for each hour
# check whether zone is going to change

# find hours when zone if going to change
# set callback on these hours

if __name__ == '__main__':
    outageBot = OutageBot()
    application = Application.builder().token('968012733:AAF3HZPm6ZjlBMVLd9KllSW17Dg7nq0Z1tw').build()
    start_handler = CommandHandler('start', outageBot.start_command)
    stop_handler = CommandHandler('stop', outageBot.stop_command)
    application.add_handler(start_handler)
    application.add_handler(stop_handler)
    application.run_polling()
