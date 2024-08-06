from typing import Awaitable, Callable

from nimbus.connections.http import HttpConnection
from nimbus.response import HttpResponse

MiddlewareHandlerType = Callable[[], Awaitable[HttpResponse | None]]
MiddlewareType = Callable[
    [HttpConnection, MiddlewareHandlerType], Awaitable[HttpResponse | None]
]


class MiddlewareManager:
    def __init__(self):
        self.middlewares: list[MiddlewareType] = []

    def add_middleware(self, middleware: MiddlewareType):
        self.middlewares.append(middleware)

    async def apply_middleware(
        self, connection: HttpConnection, handler: MiddlewareHandlerType
    ) -> HttpResponse | None:
        async def middleware_chain(index: int) -> HttpResponse | None:
            if index < len(self.middlewares):
                return await self.middlewares[index](
                    connection, lambda: middleware_chain(index + 1)
                )
            return await handler()

        return await middleware_chain(0)
