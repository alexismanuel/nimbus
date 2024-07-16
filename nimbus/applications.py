import logging
from abc import ABC, abstractmethod
from nimbus.connection import Connection
from typing import List, Tuple, Optional
from nimbus.router import Router
from nimbus.connection import Connection
from nimbus.response import HttpResponse

logger = logging.getLogger(__name__)


class ASGIApplication(ABC):
    @abstractmethod
    async def __call__(self, connection: Connection) -> None:
        pass


class NimbusApp(ASGIApplication):
    def __init__(self):
        self.routers: List[Tuple[str, Router]] = []

    def mount(self, prefix: str, router: Router):
        router.set_prefix(prefix)
        self.routers.append((prefix, router))

    async def __call__(self, connection: Connection):
        path = connection.scope['path']
        for prefix, router in self.routers:
            if path.startswith(prefix):
                response = await router(connection)
                if response:
                    return response
        
        # If no router handled the request, return a 404
        return await HttpResponse("Not Found", connection, headers={"Content-Type": "text/plain"}, status_code=404)

    def route(self, rule: str, methods: Optional[List[str]] = None):
        router = Router()
        self.mount("", router)
        return router.route(rule, methods)
