import sys

from pony.orm.core import *

import os
from decimal import Decimal
from datetime import datetime
from pathlib import Path

from pony.converting import str2datetime
from pony.orm import *
import pony.options

from util.projectRoot import projectRoot

sys.path.append(projectRoot)
pony.options.CUT_TRACEBACK = False
pony.MODE = 'INTERACTIVE'
db = Database()


class TelegramChat(db.Entity):
    chat_id = Required(int)

    user_message_list = Set("UserMessage")
    bot_message_list = Set("BotMessage")


class UserMessage(db.Entity):
    chat = Required(TelegramChat)
    create_timestamp = Required(int)
    images = Set("UserImage")
    content = Optional(str, 4000)


class UserImage(db.Entity):
    message = Required(UserMessage)
    path = Required(str)


class BotMessage(db.Entity):
    chat = Required(TelegramChat)
    create_timestamp = Required(int)

    images = Set("BotImage")
    content = Optional(str, 4000)


class BotImage(db.Entity):
    message = Required(BotMessage)
    path = Required(str)


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
