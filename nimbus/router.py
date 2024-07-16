from typing import Callable, Iterable, Optional, Dict
from werkzeug.routing import Map, Rule, RequestRedirect
from werkzeug.exceptions import MethodNotAllowed, NotFound
from nimbus.connection import Connection
from nimbus.response import HttpResponse
from nimbus.applications import ASGIApplication

class Router(ASGIApplication):
    def __init__(self):
        self.url_map = Map()
        self.endpoint_to_handler: Dict[str, Callable] = {}

    def route(self, rule: str, methods: Optional[Iterable[str]] = None, name: Optional[str] = None):
        if methods:
            methods = set(methods)
            if "OPTIONS" not in methods:
                methods.add("OPTIONS")

        def decorator(handler: Callable) -> Callable:
            self.add_route(rule, handler, name=name or handler.__name__, methods=methods)
            return handler

        return decorator

    def add_route(self, rule: str, handler: Callable, name: str, methods: Optional[Iterable[str]] = None):
        if name in self.endpoint_to_handler:
            raise ValueError(f"Duplicate route name: {name}")
        self.url_map.add(Rule(rule, endpoint=name, methods=methods))
        self.endpoint_to_handler[name] = handler

    def get_url_binding(self, connection: Connection):
        return self.url_map.bind(
            server_name=connection.headers.get('host', ''),
            path_info=connection.scope['path'],
            script_name=connection.scope.get('root_path', ''),
            url_scheme=connection.scope.get('scheme', 'http'),
            query_args=connection.scope['query_string'],
        )

    async def __call__(self, connection: Connection) -> None:
        try:
            rule, args = self.get_url_binding(connection).match(
                return_rule=True,
                method=connection.scope['method']
            )
            handler = self.endpoint_to_handler[rule.endpoint]
            await handler(connection, **args)
        except RequestRedirect as e:
            await HttpResponse(f"Redirecting to: {e.new_url}", status_code=302, headers={'Location': e.new_url})
        except MethodNotAllowed:
            await HttpResponse("Method Not Allowed", status_code=405)
        except NotFound:
            await HttpResponse("Not Found", status_code=404)