from typing import Callable, Dict, List, Optional
from werkzeug.routing import Map, Rule, MapAdapter
from nimbus.connection import Connection
from nimbus.response import HttpResponse


class Router:
    def __init__(self):
        self.url_map = Map()
        self.handlers: Dict[str, Callable] = {}
        self.prefix: str = ""
    
    def get(self, rule: str):
        return self.route(rule, ['GET'])
    
    def post(self, rule: str):
        return self.route(rule, ['POST'])
    
    def patch(self, rule: str):
        return self.route(rule, ['PATCH'])
    
    def route(self, rule: str, methods: Optional[List[str]] = None):
        def decorator(handler: Callable):
            self.add_route(rule, handler, methods)
            return handler
        return decorator

    def add_route(self, rule: str, handler: Callable, methods: Optional[List[str]] = None):
        endpoint = f"{rule}:{','.join(methods or [])}"
        self.url_map.add(Rule(rule, endpoint=endpoint, methods=methods))
        self.handlers[endpoint] = handler

    def set_prefix(self, prefix: str):
        self.prefix = prefix

    def get_adapter(self, connection: Connection) -> MapAdapter:
        return self.url_map.bind(
            server_name=connection.headers.get('host', ''),
            script_name=self.prefix,
            url_scheme=connection.scope.get('scheme', 'http'),
        )

    async def handle_request(self, connection: Connection) -> Optional[HttpResponse]:
        adapter = self.get_adapter(connection)
        try:
            endpoint, kwargs = adapter.match(
                path_info=connection.scope['path'][len(self.prefix):],
                method=connection.scope['method']
            )
            handler = self.handlers[endpoint]
            resp = await handler(connection, **kwargs)
            if isinstance(resp, HttpResponse):
                resp.connection = connection
                await resp
                return resp
        except Exception as err:
            return None  # Let the main application handle 404s and other errors

    async def __call__(self, connection: Connection) -> Optional[HttpResponse]:
        return await self.handle_request(connection)