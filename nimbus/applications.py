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
        await connection.send_response(200, 'Hello from Nimbus!', {'Content-Type': 'text/plain'})