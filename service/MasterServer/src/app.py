# coding=utf-8
import asyncio
import logging
import os
import sys

import websockets
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters


from util.projectRoot import projectRoot
sys.path.append(str(projectRoot))


from handle import chatHistory, commandHandle
from handle.chatHistory import historyWrapper
from util import configManager
from util.websocketServer import websocketHandler

from handle.chatGptHKBU import chatgpt_handle

# Enable logging
logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                    level=logging.INFO)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


# Define a few command handlers. These usually take the two arguments update and
# context.


def initApplication():
    """Start the bot."""

    # Read the token from local config file

    tel_access_token = configManager.TelegramConfig.accessToken

    # Redis database

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(tel_access_token).concurrent_updates(True).build()

    # on different commands - answer in Telegram
    commandHandle.CommandManager.registerAll(application.add_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           historyWrapper(chatgpt_handle)))

    # We use chatgpt for test this time

    # Run the bot until the user presses Ctrl-C
    logging.info("Press Ctrl + C to stop the program")
    return application


async def main():
    application = initApplication()

    await application.initialize()
    await application.start()
    websocket_server = await websockets.serve(websocketHandler, "localhost", 8000)

    # Start other asyncio frameworks here
    # Add some logic that keeps the event loop running until you want to shutdown
    # Stop the other asyncio frameworks here
    await application.updater.start_polling()
    try:
        while True:
            await asyncio.sleep(1000)
    finally:
        websocket_server.close()
        await application.updater.stop()
        await application.stop()
        await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())
