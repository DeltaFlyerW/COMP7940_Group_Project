import asyncio
import base64
import sys
import time
import logging

# Enable logging
logging.basicConfig(format='%(asctime)s %(levelname)s - %(message)s',
                    level=logging.INFO)
import httpx
import websockets
import json

from util.projectRoot import projectRoot

sys.path = [projectRoot.__str__()] + sys.path
from src.util.loggingHelper import logi
from util.configManager import MasterConfig, DiffusionConfig
from service.chatGptHKBU import ChatGPTClient


class WebsocketHandle:
    @staticmethod
    def returnEvent(serverEvent, clientEvent):
        timestamp = serverEvent['timestamp']
        clientEvent['timestamp'] = timestamp
        return json.dumps(clientEvent)

    @staticmethod
    async def userChat(event):
        result = await ChatGPTClient.get().chat(event['data']['conversation'])
        return WebsocketHandle.returnEvent(event, {
            'result': result
        })

    @staticmethod
    async def txt2img(event):
        url = f"http://{DiffusionConfig.host}:{DiffusionConfig.port}/sdapi/v1/txt2img"
        data = event['data']
        print(data)
        prompts = data.get("prompt")
        prompt = f'{prompts}' \
                 f', ethereal, realistic anime, trending on pixiv, detailed, clean lines, sharp lines, crisp lines, ' \
                 f'award winning illustration, masterpiece, 4k, eugene de blaas and ross tran, vibrant color scheme, ' \
                 f'intricately detailed'

        payload = dict(
            prompt=prompt,
            negative_prompt=data.get("negative_prompt", "ugly, tiling, poorly drawn hands, poorly drawn feet, poorly "
                                                        "drawn face, out of frame, extra limbs, disfigured, deformed, "
                                                        "body out of frame, bad anatomy, watermark, signature, "
                                                        "cut off, low contrast, underexposed, overexposed, bad art, "
                                                        "beginner, amateur, distorted face"),
            seed=-1,
            styles=["anime", 'illustration'],
            cfg_scale=7,
            steps=20,
            enable_hr=True,
            batch_size=data.get('batch_size', 1),
            denoising_strength=0.5,
        )
        response = await httpx.AsyncClient().post(url, json=payload,
                                                  headers={'Content-Type': 'application/json'},
                                                  timeout=30, follow_redirects=True, )
        if response.status_code == 200:
            response_data = response.json()

            for image in response_data['images']:
                byteImage = base64.b64decode(image)
                part = f"{event['timestamp']}\n".encode('utf-8') + byteImage
                await event['websocket'].send(part)
            return WebsocketHandle.returnEvent(event, {
                'code': 0
            })

    @staticmethod
    async def img2img(event):
        api_url = f"http://{DiffusionConfig.host}:{DiffusionConfig.port}/sdapi/v1/img2img"
        data = event['data']
        prompt = data.get("prompt")
        if not prompt:
            prompt = "perfect"
        payload = dict(
            init_images=data.get('images'),
            prompt=prompt,
            negative_prompt=data.get("negative_prompt", "ugly, out of frame, low resolution, blurry", ),
            seed=-1,
            styles=["anime"],
            cfg_scale=7,
            steps=10,
            enable_hr=True,
            batch_size=2,
            denoising_strength=0.5
        )
        response = await httpx.AsyncClient().post(api_url, json=payload,
                                                  headers={'Content-Type': 'application/json'},
                                                  timeout=10, follow_redirects=True, )

        if response.status_code == 200:
            response_data = response.json()

            for image in response_data['images']:
                byteImage = base64.b64decode(image)
                part = f"{event['timestamp']}\n".encode('utf-8') + byteImage
                await event['websocket'].send(part)
            return WebsocketHandle.returnEvent(event, {
                'code': 0
            })


async def websocket_client():
    uri = "ws://" + MasterConfig.basicUrl
    print(uri)
    ChatGPTClient.restart()
    async with websockets.connect(uri) as websocket:
        register_event = {'type': 'register', 'roles': ['chatbot', 'stable-diffusion']}
        await websocket.send(json.dumps(register_event))
        print(f"Sent: {register_event}")

        # Listen for messages from the server
        async for message in websocket:
            if isinstance(message, str):
                if message[0].startswith('{'):
                    event = json.loads(message)
                    event['websocket'] = websocket
                    # Check if 'type' is in the event and print it
                    if 'type' in event:
                        print(f"Event type: {event['type']}")

                        handle = getattr(WebsocketHandle, event['type'])
                        try:
                            result = await handle(event)
                        except Exception as e:
                            import traceback
                            traceback.print_exc()
                            await websocket.send(WebsocketHandle.returnEvent(event, {
                                "error": str(e)
                            }))
                        else:
                            await websocket.send(result)


while True:
    try:
        asyncio.run(websocket_client())
    except Exception as e:
        logi(e)
    time.sleep(3)
