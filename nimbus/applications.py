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
        self.default_router = Router()
        self.mount("", self.default_router)

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
            await self._handle_websocket(connection)
        elif isinstance(connection, HttpConnection):
            return await self._handle_http(connection)

    async def _handle_websocket(self, connection: WebSocketConnection):
        path = connection.scope["path"]
        logger.info(f"Handling WebSocket connection for path: {path}")
        handler = self.websocket_handlers.get(path)
        if handler:
            await handler(connection)
        else:
            logger.warning(f"No WebSocket handler found for path: {path}")
            await connection.close()

    async def _handle_http(self, connection: HttpConnection):
        path = connection.scope["path"]
        method = connection.scope["method"]
        logger.info(f"Handling {method} request for path: {path}")
        
        for prefix, router in self.routers:
            logger.debug(f"Checking router with prefix: '{prefix}'")
            if path.startswith(prefix):
                logger.debug(f"Attempting to route request with router: '{prefix}'")
                try:
                    response = await self.middleware_manager.apply_middleware(
                        connection, lambda: router(connection)
                    )
                    if response:
                        logger.debug(f"Router '{prefix}' handled the request")
                        return response
                except Exception as e:
                    logger.error(f"Error in router '{prefix}': {str(e)}", exc_info=True)

        logger.warning(f"No router handled the request for path: {path}")
        return await HttpResponse(
            "Not Found",
            connection,
            headers={"Content-Type": "text/plain"},
            status_code=404,
        )

    def route(self, rule: str, methods: Optional[List[str]] = None):
        return self.default_router.route(rule, methods)

    def get(self, rule: str):
        return self.route(rule, ["GET"])

    def post(self, rule: str):
        return self.route(rule, ["POST"])

    def patch(self, rule: str):
        return self.route(rule, ["PATCH"])
