import asyncio
import websockets


# create handler for each connection
async def websocketHandler(websocket, path):
    data = await websocket.recv()
    reply = f"Data recieved as:  {data}!"
    print(data)
    print(reply)
    await websocket.send(reply)



