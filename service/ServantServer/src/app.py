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


class WebsocketHandle:
    @staticmethod
    def returnEvent(serverEvent, clientEvent):
        timestamp = serverEvent['timestamp']
        clientEvent['timestamp'] = timestamp
        return json.dumps(clientEvent)

    @staticmethod
    async def userChat(event):
        from service.chatGptHKBU import ChatGPTClient
        result = await ChatGPTClient.get().chat(event['data']['conversation'])
        return WebsocketHandle.returnEvent(event, {
            'result': result
        })

    @staticmethod
    async def txt2img(event):
        url = f"http://{DiffusionConfig.host}:{DiffusionConfig.port}/sdapi/v1/txt2img"
        data = event['data']
        payload = dict(
            prompt=data.get("prompt"),
            negative_prompt=data.get("negative_prompt", "ugly, out of frame, low resolution, blurry"),
            seed=-1,
            styles=["anime"],
            cfg_scale=7,
            steps=10,
            enable_hr=True,
            batch_size=4,
            denoising_strength=0.5
        )
        response = await httpx.AsyncClient().post(url, json=payload,
                                                  headers={'Content-Type': 'application/json'},
                                                  timeout=30, follow_redirects=True, )
        if response.status_code == 200:
            response_data = response.json()
            return WebsocketHandle.returnEvent(event, {
                'result': response_data
            })

    @staticmethod
    async def img2img(event):
        api_url = f"http://{DiffusionConfig.host}:{DiffusionConfig.port}//sdapi/v1/img2img"
        data = event['data']
        payload = dict(
            init_images=data.get('images'),
            prompt=data.get("prompt", "perfect"),
            negative_prompt=data.get("negative_prompt", "ugly, out of frame, low resolution, blurry", ),
            seed=-1,
            styles=["anime"],
            cfg_scale=7,
            steps=10,
            enable_hr=True,
            batch_size=4,
            denoising_strength=0.5
        )
        response = await httpx.AsyncClient().post(api_url, json=payload,
                                                  headers={'Content-Type': 'application/json'},
                                                  timeout=10, follow_redirects=True, )

        if response.status_code == 200:
            response_data = response.json()
            return WebsocketHandle.returnEvent(event, {
                'result': response_data
            })


async def websocket_client():
    uri = "ws://" + MasterConfig.basicUrl
    print(uri)
    async with websockets.connect(uri) as websocket:
        register_event = {'type': 'register', 'roles': ['chatbot', 'stable-diffusion']}
        await websocket.send(json.dumps(register_event))
        print(f"Sent: {register_event}")

        # Listen for messages from the server
        async for message in websocket:
            if isinstance(message, str):
                print(message)
                if message[0].startswith('{'):
                    event = json.loads(message)
                    # Check if 'type' is in the event and print it
                    if 'type' in event:
                        print(f"Event type: {event['type']}")

                        handle = getattr(WebsocketHandle, event['type'])
                        try:
                            result = await handle(event)
                            print(result)
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
