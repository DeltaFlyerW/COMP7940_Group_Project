# coding=utf-8
import os
import logging
import sys

from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

from src.handle.startHandle import start
from util.projectRoot import projectRoot

sys.path.append(projectRoot)
from src.handle.chatGptHKBU import HKBUChatGPT, chatgpt_handle

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

    application.add_handler(MessageHandler(None,filters.PHOTO))
    # We use chatgpt for test this time
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chatgpt_handle))

    # Run the bot until the user presses Ctrl-C
    logging.info("Press Ctrl + C to stop the program")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
