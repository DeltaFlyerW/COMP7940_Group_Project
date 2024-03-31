import asyncio
import time

import websockets
import json


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


async def websocket_client():
    from util.configManager import MasterConfig

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
    asyncio.run(websocket_client())
    time.sleep(3)
