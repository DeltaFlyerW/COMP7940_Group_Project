import logging

import requests
import os

from telegram import Update
from telegram.ext import ContextTypes


class HKBUChatGPT:
    _instance = None

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()

        return cls._instance

    def __init__(self, config_='./config.ini'):
        """
            since we used the flyio secret. config file is no longer required
        """
        # if isinstance(config_, str):
        #     self.config = configparser.ConfigParser()
        #     self.config.read(config_)
        # elif isinstance(config_, configparser.ConfigParser):
        #     self.config = config_

    def submit(self, message: str) -> str:
        """
            This function send user's question to GPT and return the answer.
        """
        conversation = [{"role": "user", "content": message}]

        base_url = os.environ["GPT_BASE_URL"]
        model_name = os.environ["GPT_MODEL_NAME"]
        api_version = os.environ["GPT_API_VERSION"]
        access_token = os.environ["GPT_ACCESS_TOKEN"]

        # HKBU ChatGPT request full URL
        url = f"{base_url}/deployments/{model_name}/chat/completions/?api-version={api_version}"
        # Request header
        headers = {'Content-Type': 'application/json', 'api-key': access_token}
        # Request payload
        payload = {'messages': conversation}
        response = requests.post(url, json=payload, headers=headers, timeout=10)

        # With the correct response code, we will return the result
        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        # By default, it will response error
        return f"Error: {response}"


async def chatgpt_handle(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Enable the chatbot using chatgpt provided by HKBU"""

    chadId = update.effective_chat.id
    messageId = update.message.message_id

    reply_msg = HKBUChatGPT.get().submit(update.message.text)  # Send the text to ChatGPT
    logging.info("[ChatGPT] Update:  %s", update)
    logging.info("[ChatGPT] Context: %s", context)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=reply_msg)
