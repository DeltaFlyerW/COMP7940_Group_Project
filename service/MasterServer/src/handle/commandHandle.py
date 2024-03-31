import logging
from telegram import Update, ForceReply
from telegram.ext import ContextTypes, CommandHandler

from src.handle.chatGptHKBU import chatgpt_handle
from src.handle.chatHistory import historyWrapper
from src.handle.stableDiffusion import img


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
    await chatgpt_handle(update, context)



class CommandManager:
    commands = {
        start: "- Get command usage",
        clear: "- Clear your chat history.",
        regenerate: '- Regenerate last response.',
        img: "[prompt] - Generate a image with Stable Diffusion."
    }

    @classmethod
    def getHelpMessage(cls) -> str:
        help_message = "Available Commands:\n"
        for command, description in cls.commands.items():
            help_message += f"/{command.__name__} {description}\n"
        return help_message

    @classmethod
    def registerAll(cls, callback):
        for command in cls.commands.keys():
            callback(CommandHandler(command.__name__, command))

    @classmethod
    def getCommandList(cls):
        result = []
        for command, description in cls.commands.items():
            result.append((
                command.__name__, description
            ))
        return result


logging.info(CommandManager().getHelpMessage())
