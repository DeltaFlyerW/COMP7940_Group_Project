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

class TelegramUser:
    uid = Required(int)
