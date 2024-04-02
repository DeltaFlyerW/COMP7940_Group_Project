import json
import logging
import time

import httpx

from telegram import Update
from telegram.ext import ContextTypes

from src.constant import CommandType
from src.entity import ChatHistoryManager, MessageType, MessageSender
from src.handle.chatHistory import historyWrapper
from src.handle.stableDiffusion import img
from src.util.configManager import ChatbotConfig
from src.util.loggingHelper import logi
from src.util.websocketServer import ClientManager, WebsocketEvent


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


class ChatGPTDispatchClient:
    @classmethod
    def get(cls):
        return cls

    @classmethod
    async def chat(cls, conversation):
        result = await ClientManager.dispatch(
            role="chatbot",
            event=WebsocketEvent.DispatchJob("userChat", {'conversation': conversation}
                                             )
        )
        logi(result)
        return result['result']


import re


def escape_special_chars(your_string):
    # Define a function that will be used as the replacement function
    def repl(match):
        # If the match group 1 (http pattern) is not None, return it as is
        if match.group(1):
            return match.group(1)
        # Otherwise, escape the matched character
        else:
            return '\\' + match.group(0)

    # Pattern explanation (simplified version for demonstration):
    # - The part before the '|' attempts to capture a pattern that looks like a URL starting with 'http'
    # - The part after the '|' attempts to match various special characters
    # Note: This pattern is a simplified assumption of the intention behind the provided JavaScript regex.
    pattern = r'(http[^()\s]+)|([\[\]()~>#+=|{}.!-])'

    # Perform the replacement
    result = re.sub(pattern, repl, your_string, flags=re.IGNORECASE)

    return result


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

    history.append({"role": "system", "content": '''
You are a sophisticated chatbot designed to assist users in exploring and developing new hobbies such as watching movies or TV shows, hiking, cookery, and more. Your goal is to provide thoughtful, personalized recommendations and advice that cater to the interests and queries of the user. When responding, remember to:
1. **Understand the User's Request**: Carefully analyze the user's query to determine the hobby they are interested in or the kind of recommendation they are seeking.
2. **Provide Detailed Recommendations**: Offer suggestions that are specific and actionable. For example, if someone is interested in hiking, recommend trails suitable for their experience level, or if they're exploring cookery, suggest recipes based on their dietary preferences.
3. **Use Telegram Markdown for Clarity**: Format your replies using Telegram markdown to make your messages more readable. Use bold (`**text**`) for emphasis, `__italics__` for highlighting, and `[link text](URL)` for sharing useful resources.


*Incorporate Expressive Visuals*: At the end of your reply, invoke a text-to-image model (SD2) to generate a portrait that 
captures the emotion of your response. This adds a personal touch and enhances the user's interaction with you. 
suggesting some different portrait for each user base on their request.

Example"
User: "I'm looking for a new hobby, something outdoors."

Assistant: "
Exploring the great outdoors is a fantastic choice! Have you considered hiking? 
It's not only a way to enjoy nature but also a great exercise. For beginners,
I'd recommend starting with local trails that are marked as 'easy'.
Websites like AllTrails can help you find trails near you.
Also, ensure you have the right gear, especially a good pair of hiking shoes. Happy hiking! 🌲

```json
{"caption":"In case you're feeling adventurous, here's a little inspiration for you.",
"portrait":"18, female, long curly hair, smiling, casual jacket","emotion":"inspired, adventurous, ready",
"background":"mountain, forest", "gesture": "climbing"}
```
"
'''
                    }, )
    history.reverse()
    reply_msg: str = await ChatGPTDispatchClient.get().chat(history)  # Send the text to ChatGPT
    logging.info("[ChatGPT] Conversation:  %s", history)
    import re
    regex = re.compile(r'```json\s+(\{"caption.*?)```', re.DOTALL)
    promptDict = None
    caption = None
    if regex.search(reply_msg):
        try:
            promptDict = json.loads(regex.search(reply_msg).group(1))
        except:
            pass
        reply_msg = regex.sub('', reply_msg)

    entityId = ChatHistoryManager.addHistory(
        chatId=chadId, sender=MessageSender.bot, timestamp=time.time(), messageContent=reply_msg,
        messageId=0,
    )
    logi(entityId)
    logging.info("[ChatGPT] Reply: %s", reply_msg)

    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=escape_special_chars(reply_msg),
                                   parse_mode='MarkdownV2')

    if promptDict:
        if 'caption' in promptDict:
            caption = promptDict.pop('caption')
        await img(update, context, prompt="portrait, " + ','.join(promptDict.values()),
                  caption=caption, batchSize=1)
