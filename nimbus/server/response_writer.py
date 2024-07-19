import asyncio
import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class ResponseWriter:
    EVENT_HANDLERS = {
        "http.response.start": "_send_response_start",
        "http.response.body": "_send_response_body",
    }

    async def send(self, writer: asyncio.StreamWriter, event: Dict[str, Any]) -> None:
        handler_name = self.EVENT_HANDLERS.get(event["type"], "_handle_unknown_event")
        handler = getattr(self, handler_name)
        await handler(writer, event)
        await writer.drain()

    async def _send_response_start(
        self, writer: asyncio.StreamWriter, event: Dict[str, Any]
    ) -> None:
        status = event["status"]
        headers = event["headers"]
        writer.write(f"HTTP/1.1 {status}\r\n".encode())
        for name, value in headers:
            writer.write(
                f'{name.decode("ascii")}: {value.decode("ascii")}\r\n'.encode()
            )
        writer.write(b"\r\n")

    async def _send_response_body(
        self, writer: asyncio.StreamWriter, event: Dict[str, Any]
    ) -> None:
        writer.write(event["body"])

    async def _handle_unknown_event(
        self, writer: asyncio.StreamWriter, event: Dict[str, Any]
    ) -> None:
        logger.warning(f"Received unknown event type: {type(event)}")
