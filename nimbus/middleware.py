from typing import Callable, Awaitable, List
from nimbus.connection import Connection
from nimbus.response import HttpResponse

MiddlewareType = Callable[[Connection, Callable[[], Awaitable[HttpResponse]]], Awaitable[HttpResponse]]

class MiddlewareManager:
    def __init__(self):
        self.middlewares: List[MiddlewareType] = []

    def add_middleware(self, middleware: MiddlewareType):
        self.middlewares.append(middleware)

    async def apply_middleware(self, connection: Connection, handler: Callable[[], Awaitable[HttpResponse]]) -> HttpResponse:
        async def middleware_chain(index: int) -> HttpResponse:
            if index < len(self.middlewares):
                return await self.middlewares[index](connection, lambda: middleware_chain(index + 1))
            return await handler()
        
        return await middleware_chain(0)