import sys

from pony.orm.core import *

import os
from decimal import Decimal
from datetime import datetime
from pathlib import Path

from pony.converting import str2datetime
from pony.orm import *
import pony.options

from src.util.projectRoot import projectRoot

pony.options.CUT_TRACEBACK = False
pony.MODE = 'INTERACTIVE'
db = Database()


class TelegramChat(db.Entity):
    chat_id = Required(str)

    messages = Set("TelegramMessage")


class TelegramMessage(db.Entity):
    sender = Required(str)
    message_id = Optional(int)
    chat = Required(TelegramChat)
    type = Required(str)
    create_timestamp = Required(float)

    content = Optional(str, 4000)


class MessageType:
    text = "text"
    photo = "photo"


class MessageSender:
    bot = 'bot'
    user = 'user'


def initDatabase():
    from util.configManager import DatabaseConfig
    args = DatabaseConfig.toDict()
    if DatabaseConfig.provider == 'sqlite':
        args['filename'] = str(projectRoot / DatabaseConfig.filename)
        Path(args['filename']).parent.mkdir(parents=True, exist_ok=True)
        args['create_db'] = True
    db.bind(**args)
    db.generate_mapping(create_tables=True)


initDatabase()


class ChatHistoryManager:
    @classmethod
    @db_session
    def getTextHistory(cls, chatId, messageId) -> list[TelegramMessage]:
        chatId = str(chatId)
        chat = TelegramChat.get(chat_id=chatId)
        if not chat:
            chat = TelegramChat(chat_id=chatId)
            db.commit()
        result = chat.messages.select(lambda m: m.type == MessageType.text and m.message_id != messageId)
        return list(result)

    @classmethod
    @db_session
    def addHistory(cls, chatId, sender, timestamp: float, messageId=None, messageContent=None, ):
        chatId = str(chatId)
        chat = TelegramChat.get(chat_id=chatId)
        if not chat:
            chat = TelegramChat(chat_id=chatId)

        message = TelegramMessage(
            message_id=messageId,
            content=messageContent,
            chat=chat,
            type=MessageType.text,
            sender=sender,
            create_timestamp=timestamp
        )

        db.commit()
        return message.id
