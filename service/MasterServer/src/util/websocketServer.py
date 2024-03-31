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

    jobs: dict[float, dict]


class BaseWebsocketEvent:
    timestamp: float = None

    @classmethod
    def decode(cls, message):
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

    @dataclass
    class DispatchJob(BaseWebsocketEvent):
        type: str
        data: dict


class ClientManager:
    roleDict: dict[str, list[ServantClient]] = defaultdict(list)
    clients: dict[WebSocketServerProtocol, ServantClient] = {}
    jobParts: dict[float, list[bytes]] = defaultdict[list]

    @classmethod
    async def register(cls, websocket: WebSocketServerProtocol, roles: list[str]):
        client = ServantClient(websocket, roles, {})
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
    async def dispatch(cls, role: str, event: WebsocketEvent.DispatchJob):
        if len(cls.roleDict[role]) == 0:
            logi("No available role", role)
            return WebsocketEvent.Error.decode({"message": "No available role for " + role})
        client = min(cls.roleDict[role], key=lambda x: len(x.jobs))
        timestamp = time.time()
        event.timestamp = timestamp

        client.jobs[timestamp] = None
        await client.ws.send(event.dump())
        while client.jobs[timestamp] is None:
            await asyncio.sleep(0.1)

        response = client.jobs.pop(timestamp)
        if timestamp in cls.jobParts:
            response['parts'] = cls.jobParts.pop(timestamp)
        return response


# create handler for each connection
async def websocketHandler(websocket: WebSocketServerProtocol, path):
    try:
        message = await websocket.recv()

        event = WebsocketEvent.ClientRegister.decode(message)
        client = await ClientManager.register(websocket, event.roles)

        async for message in websocket:
            if isinstance(message, str):
                body = json.loads(message)
                if 'timestamp' in body:
                    client.jobs[body['timestamp']] = body
            elif isinstance(message, bytes):
                pos = message.find(b'\n')
                timestamp = message[:pos]
                part = timestamp[pos + 1:]
                ClientManager.jobParts[part].append(part)
    except Exception as e:
        logi(f"An error occurred: {e}")
    finally:
        # Remove the client from the set when they disconnect
        await ClientManager.logout(websocket)
        logi(f"Client disconnected. Total clients: {len(ClientManager.clients)}")
