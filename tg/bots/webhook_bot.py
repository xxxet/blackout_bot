import logging
from dataclasses import dataclass

from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, TypeHandler, CallbackContext, ExtBot

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


@dataclass
class WebhookUpdate:
    """Simple dataclass to wrap a custom update type"""
    user_id: int
    payload: str


class CustomContext(CallbackContext[ExtBot, dict, dict, dict]):
    """
    Custom CallbackContext class that makes `user_data` available for updates of type
    `WebhookUpdate`.
    """

    @classmethod
    def from_update(cls, update: object, application: "Application", ) -> "CustomContext":
        if isinstance(update, WebhookUpdate):
            return cls(application=application, user_id=update.user_id)
        return super().from_update(update, application)


class WebhookBot:

    def __init__(self):
        user_list = []

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Notifications  1 ")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Notifications  2 ")
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Notifications  3 ")

    async def stop(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Notifications stopped")

    # async def echo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text=update.message.text)
    #
    # async def caps(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    #     text_caps = ' '.join(context.args).upper()
    #     await context.bot.send_message(chat_id=update.effective_chat.id, text=text_caps)
    # async def send_update(self):
    #     for user in self.user_list:
    #         await context.bot.send_message(chat_id=user, text="Notifications stopped")

    async def webhook_update(self, update: WebhookUpdate, context: CustomContext) -> None:
        """Handle custom updates."""
        chat_member = await context.bot.get_chat_member(chat_id=update.user_id, user_id=update.user_id)
        payloads = context.user_data.setdefault("payloads", [])
        payloads.append(update.payload)
        combined_payloads = "</code>\n• <code>".join(payloads)
        text = (
            f"The user {chat_member.user.mention_html()} has sent a new payload. "
            f"So far they have sent the following payloads: \n\n• <code>{combined_payloads}</code>"
        )
        for user in self.user_list:
            await context.bot.send_message(chat_id=user, text=f"Notification for {user}")

        # await context.bot.send_message(chat_id=ADMIN_CHAT_ID, text=text, parse_mode=ParseMode.HTML)


if __name__ == '__main__':
    context_types = ContextTypes(context=CustomContext)
    application = (ApplicationBuilder()
                   .token('968012733:AAF3HZPm6ZjlBMVLd9KllSW17Dg7nq0Z1tw')
                   .context_types(context_types)
                   .build())
    bot = WebhookBot()

    start_handler = CommandHandler('start', bot.start)
    stop_handler = CommandHandler('stop', bot.stop)
    application.add_handler(TypeHandler(type=WebhookUpdate, callback=bot.webhook_update))
    application.add_handler(start_handler)
    application.add_handler(stop_handler)

    # echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), bot.echo)

    # schedule.every().minute.at(":50").do(bot.send_update())
    # application.add_handler(echo_handler)
    # application.add_handler(caps_handler)
    application.run_polling()
