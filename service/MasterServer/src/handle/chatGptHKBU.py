import logging
import time

import httpx

from telegram import Update
from telegram.ext import ContextTypes

from src.constant import CommandType
from src.entity import ChatHistoryManager, MessageType, MessageSender
from src.handle.chatHistory import historyWrapper
from src.util.configManager import ChatbotConfig
from src.util.loggingHelper import logi


class ChatGPTClient:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.client = httpx.AsyncClient()

    async def chat(self, conversation):
        url = f"{ChatbotConfig.basicUrl}/deployments/{ChatbotConfig.modelName}/chat/completions/" \
              f"?api-version={ChatbotConfig.apiVersion}"
        headers = {'Content-Type': 'application/json', 'api-key': ChatbotConfig.accessToken}
        payload = {'messages': conversation}

        response = await self.client.post(url, json=payload, headers=headers, timeout=10,
                                          follow_redirects=True, )

        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        return f"Error: {response.status_code}, {response.text}"

    async def close(self):
        await self.client.aclose()


async def chatgpt_handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable the chatbot using chatgpt provided by HKBU"""
    chadId = update.effective_chat.id
    messageId = update.message.message_id

    messages = ChatHistoryManager.getTextHistory(chadId, messageId)

    skipNext = False
    if update.effective_message.text == CommandType.regenerate:
        skipNext = True
        history = []
    else:
        history = [{
            'role': 'user',
            'content': update.effective_message.text
        }]
    historyLength = 0
    for message in reversed(messages):
        if skipNext:
            skipNext = False
            continue
        if message.content == CommandType.clear:
            break
        if message.content == CommandType.regenerate:
            skipNext = True
            continue
        content = message.content
        historyLength += len(content)
        if historyLength > 6000:
            break
        if message.sender == MessageSender.bot:
            history.append({
                'role': 'assistant',
                'content': content
            })
        elif message.sender == MessageSender.user:
            history.append({
                'role': 'user',
                'content': content
            })
        if len(history) > 3:
            break

    history.append({"role": "system", "content": "You are a helpful assistant. Reply in markdown format if needed."}, )
    history.reverse()
    reply_msg = await ChatGPTClient.get().chat(history)  # Send the text to ChatGPT
    logging.info("[ChatGPT] Conversation:  %s", history)
    entityId = ChatHistoryManager.addHistory(
        chatId=chadId, sender=MessageSender.bot, timestamp=time.time(), messageContent=reply_msg,
        messageId=0,
    )
    logi(entityId)
    logging.info("[ChatGPT] Reply: %s", reply_msg)

    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_msg)
