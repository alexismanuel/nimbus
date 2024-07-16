import logging
from abc import ABC, abstractmethod
from nimbus.connection import Connection
from nimbus.response import JsonResponse

logger = logging.getLogger(__name__)


class ASGIApplication(ABC):
    @abstractmethod
    async def __call__(self, connection: Connection) -> None:
        pass


class NimbusApp(ASGIApplication):
    async def __call__(self, connection: Connection) -> None:
        name = connection.query_params.get('name', 'World')
        await JsonResponse(f'Hello, {name}!', connection)