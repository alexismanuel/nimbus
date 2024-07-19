from typing import Awaitable, Callable, List

from nimbus.connections import BaseConnection
from nimbus.response import HttpResponse
from nimbus.types import MiddlewareType


class MiddlewareManager:
    def __init__(self):
        self.middlewares: List[MiddlewareType] = []

    def add_middleware(self, middleware: MiddlewareType):
        self.middlewares.append(middleware)

    async def apply_middleware(
        self, connection: BaseConnection, handler: Callable[[], Awaitable[HttpResponse]]
    ) -> HttpResponse:
        async def middleware_chain(index: int) -> HttpResponse:
            if index < len(self.middlewares):
                return await self.middlewares[index](
                    connection, lambda: middleware_chain(index + 1)
                )
            return await handler()

        return await middleware_chain(0)
