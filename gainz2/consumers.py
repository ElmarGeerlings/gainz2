import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from ai.session import guest_id_from_cookies, resolve_chat_context
from ai.ws_handlers import prepare_send_message, run_send_message_generation
from gainz2.ws_dispatch import (
    AI_WS_ENDPOINT_REGISTRY,
    WS_FORBIDDEN_RESPONSE,
    dispatch_ai_ws_endpoint,
    dispatch_ws_endpoint,
    ws_endpoint_allowed,
)


class MainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        request_id = data.get("request_id")
        endpoint = data.get("endpoint")
        attributes = data.get("attributes") or {}
        user = self.scope.get("user")

        if not ws_endpoint_allowed(user, endpoint):
            payload = {**WS_FORBIDDEN_RESPONSE, "request_id": request_id}
            await self.send(text_data=json.dumps(payload))
            return

        if endpoint == "ai/send_message":

            guest_id = guest_id_from_cookies(self.scope.get("cookies") or {})
            if not user.is_authenticated and not guest_id:
                payload = {**WS_FORBIDDEN_RESPONSE, "request_id": request_id}
                await self.send(text_data=json.dumps(payload))
                return
            ctx = resolve_chat_context(user, guest_id)
            prep = await database_sync_to_async(prepare_send_message)(ctx, attributes)
            if prep["phase"] == "generating":
                interim = prep["payload"]
                interim["request_id"] = request_id
                interim["interim"] = True
                await self.send(text_data=json.dumps(interim))
                final = await database_sync_to_async(run_send_message_generation)(
                    ctx, prep["session_id"], prep["history"]
                )
                final["request_id"] = request_id
                await self.send(text_data=json.dumps(final))
            else:
                payload = prep["payload"]
                payload["request_id"] = request_id
                await self.send(text_data=json.dumps(payload))
            return

        if endpoint in AI_WS_ENDPOINT_REGISTRY:
            guest_id = guest_id_from_cookies(self.scope.get("cookies") or {})
            payload = await database_sync_to_async(dispatch_ai_ws_endpoint)(
                user, endpoint, attributes, guest_id
            )
            payload["request_id"] = request_id
            await self.send(text_data=json.dumps(payload))
            return

        payload = await database_sync_to_async(dispatch_ws_endpoint)(
            user, endpoint, attributes
        )
        payload["request_id"] = request_id

        await self.send(text_data=json.dumps(payload))
