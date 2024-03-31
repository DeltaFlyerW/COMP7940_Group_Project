import asyncio
import time

import websockets
import json


async def websocket_client():
    from util.configManager import MasterConfig

    uri = "ws://" + MasterConfig.basicUrl
    print(uri)
    async with websockets.connect(uri) as websocket:
        # Send a registration event to the server
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


while True:
    asyncio.run(websocket_client())
    time.sleep(3)
