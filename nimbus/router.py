import logging
from typing import Any, Callable, Optional, Type

from werkzeug.routing import Map, MapAdapter, Rule

from nimbus.connections import BaseConnection, HttpConnection, WebSocketConnection
from nimbus.response import HttpResponse

logger = logging.getLogger(__name__)


class Router:
    CONNECTION_HANDLERS: dict[Type[BaseConnection], str] = {
        HttpConnection: "_handle_http_connection",
        WebSocketConnection: "_handle_websocket_connection",
    }

    def __init__(self):
        self.url_map = Map()
        self.handlers: dict[str, Callable] = {}
        self.websocket_handlers: dict[str, Callable] = {}
        self.prefix: str = ""

    def get(self, rule: str):
        return self.route(rule, ["GET"])

    def post(self, rule: str):
        return self.route(rule, ["POST"])

    def patch(self, rule: str):
        return self.route(rule, ["PATCH"])

    def route(self, rule: str, methods: Optional[list[str]] = None):
        def decorator(handler: Callable):
            self.add_route(rule, handler, methods)
            return handler

        return decorator

    def websocket(self, rule: str):
        def decorator(handler: Callable[[WebSocketConnection], Any]):
            endpoint = f"websocket:{rule}"
            self.url_map.add(Rule(rule, endpoint=endpoint))
            self.websocket_handlers[endpoint] = handler
            return handler

        return decorator

    def add_route(
        self, rule: str, handler: Callable, methods: Optional[list[str]] = None
    ):
        endpoint = f"{rule}:{','.join(methods or [])}"
        full_rule = self.prefix + rule if not rule.startswith("/") else rule
        self.url_map.add(Rule(full_rule, endpoint=endpoint, methods=methods))
        self.handlers[endpoint] = handler

    def set_prefix(self, prefix: str):
        self.prefix = prefix.rstrip("/")

    def get_adapter(self, connection: BaseConnection) -> MapAdapter:
        return self.url_map.bind(
            server_name=connection.headers.get("host", ""),
            script_name=self.prefix,
            url_scheme=connection.scope.get("scheme", "http"),
        )

    async def handle_request(
        self, connection: BaseConnection
    ) -> Optional[HttpResponse]:
        for connection_type, handler_name in self.CONNECTION_HANDLERS.items():
            if isinstance(connection, connection_type):
                handler = getattr(self, handler_name)
                return await handler(connection)

        return await self._handle_unknown_connection(connection)

    async def _handle_http_connection(
        self, connection: HttpConnection
    ) -> Optional[HttpResponse]:
        try:
            endpoint, kwargs = self._match_route(connection)
            logger.debug(f"Matched route: {endpoint}")
            handler = self.handlers[endpoint]
            response = await handler(connection, **kwargs)
            return response
        except Exception as err:
            logger.error(
                f"An error occurred while handling http connection: {str(err)}"
            )
            raise

    async def _handle_websocket_connection(
        self, connection: WebSocketConnection
    ) -> None:
        try:
            endpoint, kwargs = self._match_route(connection)
            handler = self.websocket_handlers[endpoint]
            await handler(connection, **kwargs)
        except Exception as err:
            logger.error(f"An unexpected error occurred: {str(err)}")
            raise

    async def _handle_unknown_connection(self, connection: BaseConnection) -> None:
        logger.error(f"Received unknown connection type: {type(connection)}")
        raise ValueError(f"Unsupported connection type: {type(connection)}")

    def _match_route(self, connection: BaseConnection) -> tuple:
        adapter = self.get_adapter(connection)
        path = connection.scope["path"]
        if self.prefix and path.startswith(self.prefix):
            path = path[len(self.prefix) :]
        if not path.startswith("/"):
            path = "/" + path
        method = connection.scope["method"]
        logger.debug(f"Attempting to match route: {path} with method: {method}")
        logger.debug(
            f"Available routes: {[rule.rule for rule in self.url_map.iter_rules()]}"
        )
        match = adapter.match(path_info=path, method=method)
        logger.debug(f"Matched route: {match}")
        return match

    async def __call__(self, connection: BaseConnection) -> Optional[HttpResponse]:
        return await self.handle_request(connection)
