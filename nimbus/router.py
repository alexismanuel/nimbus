import logging
from typing import Any, Callable, Dict, List, Optional, Type

from werkzeug.routing import Map, MapAdapter, Rule

from nimbus.connections import BaseConnection, HttpConnection, WebSocketConnection
from nimbus.response import HttpResponse

logger = logging.getLogger(__name__)


class Router:
    CONNECTION_HANDLERS: Dict[Type[BaseConnection], str] = {
        HttpConnection: "_handle_http_connection",
        WebSocketConnection: "_handle_websocket_connection",
    }

    def __init__(self):
        self.url_map = Map()
        self.handlers: Dict[str, Callable] = {}
        self.websocket_handlers: Dict[str, Callable] = {}
        self.prefix: str = ""

    def get(self, rule: str):
        return self.route(rule, ["GET"])

    def post(self, rule: str):
        return self.route(rule, ["POST"])

    def patch(self, rule: str):
        return self.route(rule, ["PATCH"])

    def route(self, rule: str, methods: Optional[List[str]] = None):
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
        self, rule: str, handler: Callable, methods: Optional[List[str]] = None
    ):
        endpoint = f"{rule}:{','.join(methods or [])}"
        self.url_map.add(Rule(rule, endpoint=endpoint, methods=methods))
        self.handlers[endpoint] = handler

    def set_prefix(self, prefix: str):
        self.prefix = prefix

    def get_adapter(self, connection: BaseConnection) -> MapAdapter:
        return self.url_map.bind(
            server_name=connection.headers.get("host", ""),
            script_name=self.prefix,
            url_scheme=connection.scope.get("scheme", "http"),
        )

    async def handle_request(
        self, connection: BaseConnection
    ) -> Optional[HttpResponse]:
        handler_name = self.CONNECTION_HANDLERS.get(
            type(connection), "_handle_unknown_connection"
        )
        handler = getattr(self, handler_name)
        return await handler(connection)

    async def _handle_http_connection(
        self, connection: HttpConnection
    ) -> Optional[HttpResponse]:
        try:
            endpoint, kwargs = self._match_route(connection)
            handler = self.handlers[endpoint]
            response = await handler(connection, **kwargs)
            return await self._process_http_response(response, connection)
        except Exception as err:
            logger.error(f"An error occured while handling http connection: {str(err)}")
            return HttpResponse("Internal Server Error", connection, status_code=500)

    async def _handle_websocket_connection(
        self, connection: WebSocketConnection
    ) -> None:
        try:
            endpoint, kwargs = self._match_route(connection)
            handler = self.websocket_handlers[endpoint]
            await handler(connection, **kwargs)
        except Exception as err:
            logger.error(f"An unexepected error occured: {str(err)}")
            pass

    async def _handle_unknown_connection(self, connection: BaseConnection) -> None:
        logger.error(f"Received unknow connection type: {type(connection)}")
        pass

    def _match_route(self, connection: BaseConnection) -> tuple:
        adapter = self.get_adapter(connection)
        return adapter.match(
            path_info=connection.scope["path"][len(self.prefix) :],
            method=connection.scope["method"],
        )

    async def _process_http_response(
        self, response: HttpResponse, connection: HttpConnection
    ) -> HttpResponse:
        response.connection = connection
        await response
        return response

    async def __call__(self, connection: BaseConnection) -> Optional[HttpResponse]:
        return await self.handle_request(connection)
