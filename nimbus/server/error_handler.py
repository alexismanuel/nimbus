import asyncio
import logging
from typing import Type

logger = logging.getLogger(__name__)


class ErrorHandler:
    ERROR_HANDLERS: dict[Type[BaseException], str] = {
        asyncio.CancelledError: "_handle_cancelled_error",
        asyncio.IncompleteReadError: "_handle_incomplete_read_error",
        ConnectionResetError: "_handle_connection_reset_error",
    }

    async def handle_error(
        self, error: Exception, client_addr: tuple[str, int]
    ) -> None:
        handler_name = self.ERROR_HANDLERS.get(type(error), "_handle_unknown_error")
        handler = getattr(self, handler_name)
        await handler(error, client_addr)

    async def _handle_cancelled_error(
        self, error: asyncio.CancelledError, client_addr: tuple[str, int]
    ) -> None:
        logger.info(f"Connection from {client_addr} cancelled: {str(error)}")

    async def _handle_incomplete_read_error(
        self, error: asyncio.IncompleteReadError, client_addr: tuple[str, int]
    ) -> None:
        logger.info(
            f"Client {client_addr} disconnected before sending complete request: {str(error)}"
        )

    async def _handle_connection_reset_error(
        self, error: ConnectionResetError, client_addr: tuple[str, int]
    ) -> None:
        logger.info(f"Connection reset by client {client_addr}: {str(error)}")

    async def _handle_unknown_error(
        self, error: Exception, client_addr: tuple[str, int]
    ) -> None:
        logger.error(f"Error handling connection from {client_addr}. {str(error)}")
