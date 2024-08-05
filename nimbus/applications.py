import logging
from abc import ABC, abstractmethod
from typing import Awaitable, Callable, Optional

from nimbus.connections import BaseConnection, HttpConnection, WebSocketConnection
from nimbus.middleware import MiddlewareManager, MiddlewareType
from nimbus.response import HttpResponse
from nimbus.router import Router

logger = logging.getLogger(__name__)


class ASGIApplication(ABC):
    @abstractmethod
    async def __call__(self, connection: BaseConnection) -> HttpResponse | None:
        raise NotImplementedError()


class NimbusApp(ASGIApplication):
    def __init__(self):
        self.routers: list[tuple[str, Router]] = []
        self.middleware_manager = MiddlewareManager()
        self.websocket_handlers: dict[
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

    async def __call__(self, connection: BaseConnection) -> HttpResponse | None:
        if isinstance(connection, WebSocketConnection):
            await self._handle_websocket(connection)
        elif isinstance(connection, HttpConnection):
            return await self._handle_http(connection)

    async def _handle_websocket(self, connection: WebSocketConnection) -> None:
        path = connection.scope["path"]
        logger.info(f"Handling WebSocket connection for path: {path}")
        handler = self.websocket_handlers.get(path)
        if not handler:
            logger.warning(f"No WebSocket handler found for path: {path}")
            return await connection.close()
        return await handler(connection)

    async def _handle_http(self, connection: HttpConnection) -> Optional[HttpResponse]:
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
                        return await self._process_http_response(response, connection)
                except Exception as e:
                    logger.error(f"Error in router '{prefix}'. {str(e)}")

        logger.warning(f"No router handled the request for path: {path}")
        response = HttpResponse(
            "Not Found",
            connection,
            headers={"Content-Type": "text/plain"},
            status_code=404,
        )
        return await self._process_http_response(response, connection)

    async def _process_http_response(
        self, response: HttpResponse, connection: HttpConnection
    ) -> HttpResponse:
        response.connection = connection
        await response
        return response

    def route(self, rule: str, methods: Optional[list[str]] = None):
        return self.default_router.route(rule, methods)

    def get(self, rule: str):
        return self.route(rule, ["GET"])

    def post(self, rule: str):
        return self.route(rule, ["POST"])

    def patch(self, rule: str):
        return self.route(rule, ["PATCH"])
