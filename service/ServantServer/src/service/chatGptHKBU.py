import logging
import time

import httpx

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

    async def chat(self, conversation) -> str:
        url = f"{ChatbotConfig.basicUrl}/deployments/{ChatbotConfig.modelName}/chat/completions/" \
              f"?api-version={ChatbotConfig.apiVersion}"
        print(url)
        headers = {'Content-Type': 'application/json', 'api-key': ChatbotConfig.accessToken}
        payload = {'messages': conversation}

        response = await self.client.post(url, json=payload, headers=headers, timeout=10,
                                          follow_redirects=True, )

        if response.status_code == 200:
            data = response.json()
            return data['choices'][0]['message']['content']
        logi(f"Error: {response.status_code}, {response.text}")
        return f"Error: {response.status_code}, {response.text}"

    async def close(self):
        await self.client.aclose()
