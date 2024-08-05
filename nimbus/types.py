from typing import Any, Awaitable, Callable, TypedDict

Scope = TypedDict(
    "Scope",
    {
        "type": str,
        "asgi": dict[str, Any],
        "http_version": str,
        "raw_path": bytes,
        "server": tuple[str, int],
        "client": tuple[str, int],
        "path": str,
        "headers": list[tuple[bytes, bytes]],
        "method": str,
        "query_string": bytes,
    },
)

ReceiveCallable = Callable[[int | None], Any]
SendCallable = Callable[[dict[str, Any]], Awaitable[None]]

