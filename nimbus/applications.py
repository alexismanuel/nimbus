import logging
from abc import ABC, abstractmethod
from nimbus.connection import Connection

logger = logging.getLogger(__name__)


class ASGIApplication(ABC):
    @abstractmethod
    async def __call__(self, connection: Connection) -> None:
        pass


class NimbusApp(ASGIApplication):
    async def __call__(self, connection: Connection) -> None:
        name = connection.query_params.get('name', 'World')
        greeting = f'Hello, {name}!'
        await connection.send_response(200, greeting, {'Content-Type': 'text/plain'})