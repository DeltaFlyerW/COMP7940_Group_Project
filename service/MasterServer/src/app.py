# coding=utf-8
import asyncio
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                    level=logging.INFO)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

import sys

import websockets
from telegram.ext import Application, MessageHandler, filters

from util.projectRoot import projectRoot

sys.path.append(str(projectRoot))

from telegram import Bot, BotCommand

from src.handle import commandHandle
from src.handle.chatHistory import historyWrapper
from src.util import configManager
from src.util.websocketServer import websocketHandler

from src.handle.chatGptHKBU import chatgpt_handle


# Define a few command handlers. These usually take the two arguments update and
# context.


def initApplication():
    """Start the bot."""

    # Read the token from local config file

    tel_access_token = configManager.TelegramConfig.accessToken

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(tel_access_token).concurrent_updates(True).build()

    # on different commands - answer in Telegram
    commandHandle.CommandManager.registerAll(application.add_handler)

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,
                                           historyWrapper(chatgpt_handle)))

    bot = Bot(token=tel_access_token, )

    # We use chatgpt for test this time

    # Run the bot until the user presses Ctrl-C
    logging.info("Press Ctrl + C to stop the program")
    return application, bot


async def main():
    logging.info("Application initialization")
    application, bot = initApplication()

    await application.initialize()
    await application.start()
    await bot.set_my_commands(commandHandle.CommandManager.getCommandList())

    websocket_server = await websockets.serve(websocketHandler, "0.0.0.0", 4534)

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
