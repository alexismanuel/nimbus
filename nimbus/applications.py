import logging
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Dict, List, Optional, Tuple

from nimbus.connections import BaseConnection, HttpConnection, WebSocketConnection
from nimbus.middleware import MiddlewareManager, MiddlewareType
from nimbus.response import HttpResponse
from nimbus.router import Router
from nimbus.types import ReceiveCallable, Scope, SendCallable

logger = logging.getLogger(__name__)


class ASGIApplication(ABC):
    @abstractmethod
    async def __call__(
        self, scope: Scope, receive: ReceiveCallable, send: SendCallable
    ) -> None:
        pass


class NimbusApp(ASGIApplication):
    def __init__(self):
        self.routers: List[Tuple[str, Router]] = []
        self.middleware_manager = MiddlewareManager()
        self.websocket_handlers: Dict[
            str, Callable[[WebSocketConnection], Awaitable[None]]
        ] = {}

    def mount(self, prefix: str, router: Router):
        router.set_prefix(prefix)
        self.routers.append((prefix, router))

    def add_middleware(self, middleware: MiddlewareType):
        self.middleware_manager.add_middleware(middleware)

    def websocket(self, path: str):
        def decorator(handler: Callable[[WebSocketConnection], Awaitable[None]]):
            self.websocket_handlers[path] = handler
            return handler

        return decorator

    async def __call__(self, connection: BaseConnection):
        if isinstance(connection, WebSocketConnection):
            path = connection.scope["path"]
            handler = self.websocket_handlers.get(path)
            if handler:
                await handler(connection)
            else:
                await connection.close()
        elif isinstance(connection, HttpConnection):
            path = connection.scope["path"]
            for prefix, router in self.routers:
                if path.startswith(prefix):
                    response = await self.middleware_manager.apply_middleware(
                        connection, lambda: router(connection)
                    )
                    if response:
                        return response

            # If no router handled the request, return a 404
            return await HttpResponse(
                "Not Found",
                connection,
                headers={"Content-Type": "text/plain"},
                status_code=404,
            )

    def route(self, rule: str, methods: Optional[List[str]] = None):
        router = Router()
        self.mount("", router)
        return router.route(rule, methods)
