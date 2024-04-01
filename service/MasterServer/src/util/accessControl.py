import time

from telegram import Update
from telegram.ext import ContextTypes

from src.util.websocketServer import ClientManager


def accessWrapper(func, timeout=60):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chatId = update.effective_chat.id
        timestamp = time.time()
        if chatId in ClientManager.workingChatIdSet:
            dis = int(timestamp - ClientManager.workingChatIdSet[chatId])
            if dis < timeout:
                await context.bot.send_message(chatId, f"Your request are processing...({dis}s ago)")
                return
        result = await func(update, context)
        ClientManager.workingChatIdSet.pop(chatId)
        return result

    wrapped.__name__ = func.__name__
    return wrapped
