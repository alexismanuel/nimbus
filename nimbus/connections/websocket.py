from typing import Optional, Union

from nimbus.types import ReceiveCallable, Scope, SendCallable

from .base import BaseConnection


class WebSocketConnection(BaseConnection):
    def __init__(self, scope: Scope, receive: ReceiveCallable, send: SendCallable):
        super().__init__(scope, receive, send)
        self.accepted = False
        self.closed = False

    async def accept(self) -> None:
        await self.send({"type": "websocket.accept"})
        self.accepted = True

    async def send_message(self, message: Union[str, bytes]) -> None:
        event_type = "text" if isinstance(message, str) else "bytes"
        await self.send({"type": "websocket.send", event_type: message})

    async def receive_message(self) -> Optional[Union[str, bytes]]:
        event = await self.receive(-1)
        if event["type"] == "websocket.receive":
            return event.get("text") or event.get("bytes")
        if event["type"] == "websocket.disconnect":
            self.closed = True
            return None
        raise ValueError(f"Unexpected WebSocket event: {event['type']}")

    async def close(self, code: int = 1000) -> None:
        if not self.closed:
            await self.send({"type": "websocket.close", "code": code})
            self.closed = True
