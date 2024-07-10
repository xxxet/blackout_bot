import logging
from datetime import datetime

import pytz
from telegram import Update
from telegram.ext import CommandHandler, Application, ContextTypes

import config
from sql.sql_service import GroupService, SubsService, UserService
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
        chat_id = context.job.chat_id
        grp = context.job.data
        _, msg = self.get_time_finder(grp).find_next_remind_time(notify_before=self.before_time)
        await context.bot.send_message(chat_id=chat_id, text=f"Notification for {grp}:\n" + msg)
        remind_time, _ = self.get_time_finder(grp).find_next_remind_time(notify_before=self.before_time,
                                                                         time_delta=self.before_time + 5)
        context.job_queue.run_once(self.notification, name=str(chat_id), when=remind_time,
                                   data=grp, chat_id=chat_id)

    async def stop_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        req_group = " ".join(context.args)
        if req_group == "":
            await update.message.reply_text(f'Stop command should be used with group name')
            return
        if context.job_queue.get_jobs_by_name(str(chat_id)):
            list(map(lambda job: job.schedule_removal(),
                     filter(lambda job: job.data == req_group, context.job_queue.get_jobs_by_name(str(chat_id)))))
            await update.message.reply_text(f'Stopped reminder for chat id: {chat_id}')
        else:
            await update.message.reply_text(f'No job found for chat id: {chat_id}')

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(f'Available commands:\n/start \n'
                                        f'/stop group_name \n'
                                        f'/subscribe group_name')

    async def subscribe_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        req_group = " ".join(context.args)
        if req_group == "":
            await update.message.reply_text(f'Subscribe command should be used with group name')
            return
        session_maker = config.get_session_maker()
        with session_maker() as session:
            grp_serv = GroupService(session)
            grp = grp_serv.get_group(req_group)
            if grp is None:
                await update.message.reply_text(f'No such group {req_group} added yet')
                return
            sub_serv = SubsService(session)
            user_serv = UserService(session)
            user = user_serv.add(str(chat_id))
            sub_serv.add(user, grp)
            await update.message.reply_text(f'You are subscribed to {req_group}')
            remind_time, _ = self.get_time_finder(req_group).find_next_remind_time(notify_before=self.before_time)
            context.job_queue.run_once(self.notification, name=str(chat_id), when=remind_time,
                                       data=grp, chat_id=chat_id)

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.message.chat_id
        session_maker = config.get_session_maker()
        with session_maker() as session:
            sub_serv = SubsService(session)
            user_serv = UserService(session)
            user = user_serv.get_user(chat_id)
            subs = sub_serv.get_subs_for_user(user)
            if len(subs) == 0:
                await update.message.reply_text(f'You are not subscribed, {chat_id}')
            for sub in subs:
                _, msg = self.get_time_finder(sub.group.group_name).find_next_remind_time(
                    notify_before=self.before_time)
                await update.message.reply_text(msg)

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


def main(token):
    outage_bot = OutageBot()
    application = Application.builder().token(token).build()
    start_handler = CommandHandler('start', outage_bot.start_command)
    subscribe_handler = CommandHandler('subscribe', outage_bot.subscribe_command)
    stop_handler = CommandHandler('stop', outage_bot.stop_command)
    status_command = CommandHandler('status', outage_bot.status_command)
    jobs_command = CommandHandler('jobs', outage_bot.jobs_command)
    application.add_handler(start_handler)
    application.add_handler(subscribe_handler)
    application.add_handler(stop_handler)
    application.add_handler(status_command)
    application.add_handler(jobs_command)
    application.run_polling()
