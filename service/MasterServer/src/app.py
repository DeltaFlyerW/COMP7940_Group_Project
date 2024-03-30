# coding=utf-8
import os
import logging
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from ChatGPT_HKBU import HKBUChatGPT

# Global variable
REDIS = None

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )



async def equipped_chatgpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable the chatbot using chatgpt provided by HKBU"""
    chatgpt = HKBUChatGPT()
    reply_msg = chatgpt.submit(update.message.text)  # Send the text to ChatGPT
    logging.info("[ChatGPT] Update:  %s", update)
    logging.info("[ChatGPT] Context: %s", context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_msg)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)
    # Use lazy % formatting in logging functions
    logging.info("[Echo] Update:  %s", update)
    logging.info("[Echo] Context: %s", context)





def main() -> None:
    """Start the bot."""

    # Read the token from local config file

    tel_access_token = os.environ["TEL_ACCESS_TOKEN"]

    # Redis database
    redis_host = os.environ["REDIS_HOST"]
    redis_port = os.environ["REDIS_PORT"]
    redis_passwd = os.environ["REDIS_PASSWD"]


    # Create the Application and pass it your bot's token.
    application = Application.builder().token(tel_access_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))

    # We use chatgpt for test this time
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, equipped_chatgpt))

    # Run the bot until the user presses Ctrl-C
    logging.info("Press Ctrl + C to stop the program")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
