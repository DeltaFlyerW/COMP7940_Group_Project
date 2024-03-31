import asyncio
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable

import jsonpickle

from websockets import WebSocketServerProtocol

from .loggingHelper import logi


@dataclass
class ServantClient:
    ws: WebSocketServerProtocol
    roles: list[str]

    jobs: dict[float, Callable]


class BaseWebsocketEvent:
    timestamp: float = None

    @classmethod
    def decode(cls, message: str | dict):
        if isinstance(message, str):
            message = json.loads(message)
        result = cls
        for key, value in message.items():
            setattr(result, key, value)
        return result

    def dump(self):
        if self.timestamp is None:
            self.timestamp = time.time()
        return jsonpickle.encode(self, unpicklable=False, make_refs=False)


class WebsocketEvent:
    class ClientRegister(BaseWebsocketEvent):
        roles: list[str]

    class Error(BaseWebsocketEvent):
        message: str


class ClientManager:
    roleDict: dict[str, list[ServantClient]] = defaultdict(list)
    clients: dict[WebSocketServerProtocol, ServantClient] = {}

    @classmethod
    async def register(cls, websocket: WebSocketServerProtocol, roles: list[str]):
        client = ServantClient(websocket, roles, [])
        logi(roles, message="Servant registered", )
        cls.clients[websocket] = client
        for role in client.roles:
            cls.roleDict[role].append(client)
        return client

    @classmethod
    async def logout(cls, websocket: WebSocketServerProtocol):
        if websocket in cls.clients:
            client = cls.clients[websocket]
            for role in client.roles:
                if client in cls.roleDict[role]:
                    cls.roleDict[role].remove(client)
            cls.clients.pop(websocket)

    @classmethod
    async def dispatch(cls, role: str, event: BaseWebsocketEvent, callback):
        if len(cls.roleDict[role]) == 0:
            logi("No available role", role)
            return WebsocketEvent.Error.decode({"message": "No available role for " + role})
        client = min(cls.roleDict[role], key=lambda x: len(x.jobs))
        timestamp = time.time()
        event.timestamp = timestamp
        client.jobs[timestamp] = callback
        await client.ws.send(event.dump())


# create handler for each connection
async def websocketHandler(websocket: WebSocketServerProtocol, path):
    try:
        message = await websocket.recv()

        event = WebsocketEvent.ClientRegister.decode(message)
        client = await ClientManager.register(websocket, event.roles)

        async for message in websocket:
            body = json.loads(message)
            if 'timestamp' in body:
                client.jobs[body['timestamp']](body)
    except Exception as e:
        logi(f"An error occurred: {e}")
    finally:
        # Remove the client from the set when they disconnect
        await ClientManager.logout(websocket)
        logi(f"Client disconnected. Total clients: {len(ClientManager.clients)}")
