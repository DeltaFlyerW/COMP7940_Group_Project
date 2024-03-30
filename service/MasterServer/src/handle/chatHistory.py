import time

from telegram import Update
from telegram.ext import ContextTypes


def historyWrapper(func):
    async def wrapped(update: Update, context: ContextTypes.DEFAULT_TYPE):
        handle(update, context)
        return await func(update, context)

    wrapped.__name__ = func.__name__
    return wrapped


def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from src.entity import ChatHistoryManager, MessageSender
    ChatHistoryManager.addHistory(
        update.effective_chat.id,
        MessageSender.user,
        update.effective_message.date.timestamp(),
        update.effective_message.message_id,
        update.effective_message.text
    )
