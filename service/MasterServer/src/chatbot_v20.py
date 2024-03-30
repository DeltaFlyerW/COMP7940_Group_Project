# coding=utf-8
import os
import logging
import redis
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from ChatGPT_HKBU import HKBUChatGPT

# Global variable
REDIS = None

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

# set higher logging level for httpx to avoid all GET and POST requests being logged
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)



# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def hello_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /hello is issued."""
    user = context.args[0]
    await update.message.reply_text(f"Good day, {user}!")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text("Help!")


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /add is issued."""
    try:
        logging.info("Context %s", context.args[0])
        msg = context.args[0]
        REDIS.incr(msg)
        times = REDIS.get(msg).decode("UTF-8")
        await update.message.reply_text(f"You have said { msg } for { times } times")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /add <keyword>")

async def get_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message of the value when the command /get is issued."""
    try:
        logging.info("[Get_Command] Context %s", context.args)
        key = context.args[0]
        ret = REDIS.get(key)
        if ret:
            value = ret.decode("UTF-8")
            await update.message.reply_text(f"Key: {key}, Value: {value}")
        else:
            await update.message.reply_text(f"Error occurred ! No such key: '{key}'")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /get <key> \n"
                                        "It will return the value of the corresponding key")

async def set_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /set is issued."""
    try:
        list_tmp = None
        key      = None
        value    = None
        if len(context.args) > 1:
            list_tmp = context.args
            key      = list_tmp[0]
            value    = list_tmp[2]
        else:
            list_tmp = context.args[0].split("=")
            key      = list_tmp[0]
            value    = list_tmp[1]

        logging.info("[Set_Command] Context %s list_tmp %s Key %s, Value %s", context.args, list_tmp, key, value)
        ret = REDIS.set(key, value)

        if ret:
            await update.message.reply_text(f"Setting {key}={value}, Done!")
        else:
            await update.message.reply_text("Error occurred! The key may already exist.")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /set <key>=<value> \n"
                                        "It will set the key-value pair")



async def del_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /del is issued."""

    try:
        logging.info("[Del_Command] Context %s", context.args[0])
        key = context.args[0]
        ret = REDIS.get(key)

        if ret:
            value = ret.decode("UTF-8")
            REDIS.delete(key)
            await update.message.reply_text(f"Deleting {key}={value}, Done!")
        else:
            await update.message.reply_text(f"Error occurred ! No such key '{key}'")
    except (IndexError, ValueError):
        await update.message.reply_text("Usage: /del <key> \n"
                                        "It will delete the key-value pair")


async def equipped_chatgpt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable the chatbot using chatgpt provided by HKBU"""
    chatgpt = HKBUChatGPT()
    reply_msg = chatgpt.submit(update.message.text) # Send the text to ChatGPT
    logging.info("[ChatGPT] Update:  %s", update)
    logging.info("[ChatGPT] Context: %s", context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_msg)

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    await update.message.reply_text(update.message.text)
    # Use lazy % formatting in logging functions
    logging.info("[Echo] Update:  %s", update)
    logging.info("[Echo] Context: %s", context)



def init_redis(host: str, port: int, passwd: str) -> None:
    """ Init the redis database  """
    # Update redis with correct parameters
    global REDIS
    REDIS = redis.Redis(host=host, port=port, password=passwd)

def main() -> None:
    """Start the bot."""


    # Read the token from local config file
    
    tel_access_token = os.environ["TEL_ACCESS_TOKEN"]

    # Redis database
    redis_host   = os.environ["REDIS_HOST"]
    redis_port   = os.environ["REDIS_PORT"]
    redis_passwd = os.environ["REDIS_PASSWD"]

    init_redis(redis_host, redis_port, redis_passwd)

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(tel_access_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("get", get_command))
    application.add_handler(CommandHandler("set", set_command))
    application.add_handler(CommandHandler("del", del_command))

    application.add_handler(CommandHandler("hello", hello_command))

    # We use chatgpt for test this time
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, equipped_chatgpt))


    # logging.info("Do you want to enable ChatGPT [Yes / No] (Default = No): ")

    # ans = input()

    # if  ans in ('Yes', 'YES', 'yes', 'Y', 'y'):
    #     # on non command i.e message - using chatgpt.
    #     logging.info("Using ChatGPT")
    #     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, equipped_chatgpt))
    # elif ans in ('No', 'NO', 'no', 'N', 'n'):
    #     # on non command i.e message - echo the message on Telegram
    #     logging.info("Echo message only")
    #     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    # else:
    #     logging.warning("Please type 'Yes', 'Y', 'y','yes' or 'No', 'no', 'N', 'n'\n "
    #                     "Input directionality is unknown, default is used\n"
    #                     "Try rerun the program with correct input if you want to enable ChatGPT")
    #     application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C      
    logging.info("Press Ctrl + C to stop the program")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
