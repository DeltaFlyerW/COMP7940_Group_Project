import base64
from io import BytesIO

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from src.util.websocketServer import ClientManager, WebsocketEvent


async def img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = context.args[0]
    response = await ClientManager.dispatch("stable-diffusion",
                                            WebsocketEvent.DispatchJob("txt2img", {'prompt': prompt}
                                                                       )
                                            )
    result = response['result']
    media = []
    for base64_str in result['images']:
        # Decode the base64 string
        img_data = base64.b64decode(base64_str)
        # Convert to a BytesIO buffer
        bio = BytesIO(img_data)
        bio.name = 'image.png'
        # Reset the buffer position to the start
        bio.seek(0)
        # Append to the media list as InputMediaPhoto
        media.append(InputMediaPhoto(media=bio))

    # Send media group
    context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
