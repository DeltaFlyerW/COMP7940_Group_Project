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

    messages = Set("TelegramMessage")


class TelegramMessage(db.Entity):
    sender = Required(str)
    chat = Required(TelegramChat)
    type = Required(str)
    create_timestamp = Required(float)

    images = Set('TelegramImage')
    content = Optional(str, 4000)



class TelegramImage(db.Entity):
    message = Required(TelegramMessage)
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
