import logging
from typing import Dict, Optional, Type

from nimbus.connections import BaseConnection, HttpConnection, WebSocketConnection
from nimbus.response import HttpResponse

logger = logging.getLogger(__name__)


class ConnectionHandler:
    CONNECTION_HANDLERS: Dict[Type[BaseConnection], str] = {
        HttpConnection: "_handle_http_connection",
        WebSocketConnection: "_handle_websocket_connection",
    }

    async def handle_connection(
        self, connection: BaseConnection
    ) -> Optional[HttpResponse]:
        handler_name = self.CONNECTION_HANDLERS.get(
            type(connection), "_handle_unknown_connection"
        )
        handler = getattr(self, handler_name)
        await handler(connection)

    async def _handle_http_connection(
        self, connection: HttpConnection
    ) -> Optional[HttpResponse]:
        if not connection.started:
            return await HttpResponse(
                "Internal Server Error",
                connection,
                headers={"Content-Type": "text/plain"},
                status_code=500,
            )

        if not connection.finished:
            return await HttpResponse("", connection, headers={}, status_code=200)

        return None  # If the response was properly started and finished, we don't need to do anything

    async def _handle_websocket_connection(
        self, connection: WebSocketConnection
    ) -> None:
        if not connection.accepted and not connection.closed:
            await connection.close(1000)  # Normal closure

    async def _handle_unknown_connection(self, connection: BaseConnection) -> None:
        logger.warning(f"Received unknown connection type: {type(connection)}")
