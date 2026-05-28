import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from gainz2.ws_dispatch import dispatch_ws_endpoint


class MainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        request_id = data.get("request_id")
        endpoint = data.get("endpoint")
        attributes = data.get("attributes") or {}
        payload = await database_sync_to_async(dispatch_ws_endpoint)(
            self.scope.get("user"), endpoint, attributes
        )
        payload["request_id"] = request_id

        await self.send(text_data=json.dumps(payload))