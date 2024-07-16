import logging
from abc import ABC, abstractmethod
from nimbus.connection import Connection

logger = logging.getLogger(__name__)


class ASGIApplication(ABC):
    @abstractmethod
    async def __call__(self, connection: Connection) -> None:
        pass
