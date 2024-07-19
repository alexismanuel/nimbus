from typing import Any, Awaitable, Callable, Dict, TypedDict

from typing_extensions import Protocol

Scope = TypedDict(
    "Scope",
    {
        "type": str,
        "path": str,
        "headers": list[tuple[bytes, bytes]],
        "method": str,
        "query_string": bytes,
    },
)

ReceiveCallable = Callable[[], Any]
SendCallable = Callable[[Dict[str, Any]], None]


class BaseConnection(Protocol):
    scope: Scope
    receive: ReceiveCallable
    send: SendCallable


class HttpResponse(Protocol):
    pass


MiddlewareType = Callable[
    [BaseConnection, Callable[[], Awaitable[HttpResponse]]], Awaitable[HttpResponse]
]
