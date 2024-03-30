from pony.orm.core import *

import os
from decimal import Decimal
from datetime import datetime
from pathlib import Path

from pony.converting import str2datetime
from pony.orm import *
import pony.options

pony.options.CUT_TRACEBACK = False
pony.MODE = 'INTERACTIVE'
db = Database()


class TelegramChat(db.Entity):
    chat_id = Required(int)

    user_message_list = Set("ChatMessage")
    bot_message_list = Set("ChatMessage")


class ChatMessage(db.Entity):
    sender = Required(str)
    chat = Required(TelegramChat)
    create_timestamp = Required(int)

    images = Set("UserImage")
    content = Optional(str, 4000)


class ChatImage(db.Entity):
    message = Required(ChatMessage)
    path = Required(str)
