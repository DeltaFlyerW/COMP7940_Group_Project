from telegram import Update, ForceReply
from telegram.ext import ContextTypes, CommandHandler

import src.handle.chatGptHKBU
from src.handle.chatHistory import historyWrapper


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        f"Hi {user.mention_html()}!, \n"
        f"{CommandManager.getHelpMessage()}",
        reply_markup=ForceReply(selective=True),
    )


@historyWrapper
async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Your chat history has been cleared.")


@historyWrapper
async def regenerate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    await update.message.reply_text("Regenerating...")
    await src.handle.chatGptHKBU.chatgpt_handle(update, context)


class CommandManager:
    commands = {
        start: "Get command usage",
        clear: "Clear your chat history.",
        regenerate: 'Regenerate last response.'
    }

    @classmethod
    def getHelpMessage(cls) -> str:
        help_message = "Available Commands:\n"
        for command, description in cls.commands.items():
            help_message += f"/{command.__name__} - {description}\n"
        return help_message

    @classmethod
    def registerAll(cls, callback):
        for command in cls.commands.keys():
            callback(CommandHandler(command.__name__, command))


print(CommandManager().getHelpMessage())
