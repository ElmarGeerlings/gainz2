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
        user = self.scope.get("user")

        if endpoint == "ai/send_message":
            from ai.ws_handlers import prepare_send_message, run_send_message_generation

            prep = await database_sync_to_async(prepare_send_message)(user, attributes)
            if prep["phase"] == "generating":
                interim = prep["payload"]
                interim["request_id"] = request_id
                interim["interim"] = True
                await self.send(text_data=json.dumps(interim))
                final = await database_sync_to_async(run_send_message_generation)(
                    user, prep["session_id"], prep["history"]
                )
                final["request_id"] = request_id
                await self.send(text_data=json.dumps(final))
            else:
                payload = prep["payload"]
                payload["request_id"] = request_id
                await self.send(text_data=json.dumps(payload))
            return

        payload = await database_sync_to_async(dispatch_ws_endpoint)(
            user, endpoint, attributes
        )
        payload["request_id"] = request_id

        await self.send(text_data=json.dumps(payload))
