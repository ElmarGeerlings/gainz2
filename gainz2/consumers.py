import json

from channels.generic.websocket import AsyncWebsocketConsumer


class MainConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        request_id = data.get("request_id")
        endpoint = data.get("endpoint")
        attributes = data.get("attributes") or {}

        if endpoint == "ping":
            payload = {
                'request_id': request_id,
                'status': 200,
                'headers': [],
                'html_content': None,
                'json_content': {'message': 'pong', 'echo_attributes': attributes},
            }
        else:
            payload = {
                "request_id": request_id,
                "status": 404,
                "headers": [],
                "html_content": None,
                "json_content": {"error": f"unknown endpoint: {endpoint}"},
            }

        await self.send(text_data=json.dumps(payload))