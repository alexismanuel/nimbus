from typing import Type

from nimbus.exceptions import UnsupportedConnectionType
from nimbus.types import ReceiveCallable, Scope, SendCallable

from .base import BaseConnection
from .http import HttpConnection
from .websocket import WebSocketConnection

CONNECTION_TYPES: dict[str, Type[BaseConnection]] = {
    "http": HttpConnection,
    "websocket": WebSocketConnection,
}


def create_connection(
    scope: Scope, receive: ReceiveCallable, send: SendCallable
) -> BaseConnection:
    connection_class = CONNECTION_TYPES.get(scope["type"])
    if connection_class is None:
        raise UnsupportedConnectionType(f"Unsupported connection type: {scope['type']}")
    return connection_class(scope, receive, send)
