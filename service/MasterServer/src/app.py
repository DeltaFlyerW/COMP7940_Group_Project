# coding=utf-8
import logging
import os
import sys

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from src.handle import chatHistory, commandHandle
from src.handle.chatHistory import historyWrapper
from src.util import configManager
from util.projectRoot import projectRoot

sys.path.append(projectRoot)
from src.handle.chatGptHKBU import chatgpt_handle

# Enable logging
logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                    level=logging.INFO)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.


def main() -> None:
    """Start the bot."""

    # Read the token from local config file

    tel_access_token = configManager.TelegramConfig.accessToken

    # Redis database

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(tel_access_token).build()

    # on different commands - answer in Telegram
    commandHandle.CommandManager.registerAll(application.add_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           historyWrapper(chatgpt_handle)))

    # We use chatgpt for test this time

    # Run the bot until the user presses Ctrl-C
    logging.info("Press Ctrl + C to stop the program")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
