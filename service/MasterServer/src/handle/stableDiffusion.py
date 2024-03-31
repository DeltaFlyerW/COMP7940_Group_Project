import base64
from io import BytesIO

from telegram import Update, InputMediaPhoto
from telegram.ext import ContextTypes

from src.util.websocketServer import ClientManager, WebsocketEvent

from PIL import Image
from io import BytesIO


def resize_image(image_bytes, max_length=256):
    # Convert the bytearray to a file-like object
    img_input = BytesIO(image_bytes)

    # Open the image
    img = Image.open(img_input)

    # Calculate the new size, keeping the aspect ratio
    if img.width > img.height:
        new_width = max_length
        new_height = int(max_length * img.height / img.width)
    else:
        new_height = max_length
        new_width = int(max_length * img.width / img.height)

    # Resize the image
    img_resized = img.resize((new_width, new_height))

    # Convert the image to JPEG
    img_output = BytesIO()
    img_resized.save(img_output, format='JPEG', quality=85)  # You can adjust the quality

    # Return the image data as a bytearray
    return img_output.getvalue()


async def img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatId = update.effective_chat.id
    if chatId in ClientManager.workingChatIdSet:
        await context.bot.send_message(chatId, "Your images are generating...")
        return
    else:
        ClientManager.workingChatIdSet.add(chatId)
    ClientManager.workingChatIdSet.add(update.effective_chat.id)

    prompt = ','.join(context.args)
    response = await ClientManager.dispatch("stable-diffusion",
                                            WebsocketEvent.DispatchJob("txt2img", {'prompt': prompt}
                                                                       )
                                            )
    media = []
    for img_data in response['parts']:
        bio = BytesIO(img_data)
        bio.name = 'image.png'
        # Reset the buffer position to the start
        bio.seek(0)
        # Append to the media list as InputMediaPhoto
        media.append(InputMediaPhoto(media=bio))

    # Send media group

    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
    ClientManager.workingChatIdSet.remove(chatId)


async def img2img(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chatId = update.effective_chat.id
    if chatId in ClientManager.workingChatIdSet:
        await context.bot.send_message(chatId, "Your images are generating...")
        return
    else:
        ClientManager.workingChatIdSet.add(chatId)
    photo_list = update.message.photo
    images = []
    for photo in photo_list:
        file = await photo.get_file()
        imageByteArray = await file.download_as_bytearray()
        jpegBytes = resize_image(imageByteArray)
        images.append(base64.b64encode(jpegBytes))
    response = await ClientManager.dispatch("stable-diffusion",
                                            WebsocketEvent.DispatchJob("img2img", {'init_images': images,
                                                                                   'prompt': update.message.caption
                                                                                   }
                                                                       )
                                            )

    media = []
    for img_data in response['parts']:
        bio = BytesIO(img_data)
        bio.name = 'image.png'
        # Reset the buffer position to the start
        bio.seek(0)
        # Append to the media list as InputMediaPhoto
        media.append(InputMediaPhoto(media=bio))
    await context.bot.send_media_group(chat_id=update.effective_chat.id, media=media)
    ClientManager.workingChatIdSet.remove(chatId)
