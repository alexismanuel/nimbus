import asyncio
import logging
from typing import Optional

from nimbus.applications import ASGIApplication
from nimbus.connections import create_connection
from nimbus.response import HttpResponse
from nimbus.utils import create_ssl_context

from .connection_handler import ConnectionHandler
from .error_handler import ErrorHandler
from .request_parser import RequestParser
from .response_writer import ResponseWriter

logger = logging.getLogger(__name__)


class NimbusServer:
    def __init__(
        self,
        app: ASGIApplication,
        host: str = "127.0.0.1",
        port: int = 8000,
        ssl_keyfile: Optional[str] = None,
        ssl_certfile: Optional[str] = None,
    ):
        self.app = app
        self.host = host
        self.port = port
        self.ssl_context = (
            create_ssl_context(ssl_keyfile, ssl_certfile)
            if ssl_keyfile and ssl_certfile
            else None
        )
        self.request_parser = RequestParser()
        self.response_writer = ResponseWriter()
        self.connection_handler = ConnectionHandler()
        self.error_handler = ErrorHandler()

    async def handle_connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        client_addr = writer.get_extra_info("peername")
        logger.info(f"New connection from {client_addr}")
        try:
            await self._process_connection(reader, writer, client_addr)
        except Exception as e:
            await self.error_handler.handle_error(e, client_addr)
        finally:
            await self._close_connection(writer, client_addr)

    async def _process_connection(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        client_addr: tuple[str, int],
    ) -> None:
        method, path, headers = await self.request_parser.parse_request(reader)
        scope = self.request_parser.create_scope(
            method, path, headers, (self.host, self.port), client_addr
        )
        connection = create_connection(
            scope, reader.read, self._create_send_function(writer)
        )
        await self.app(connection)
        response = await self.connection_handler.handle_connection(connection)
        if isinstance(response, HttpResponse):
            await self._send_response(writer, response)

    def _create_send_function(self, writer: asyncio.StreamWriter):
        return lambda event: self.response_writer.send(writer, event)

    async def _send_response(
        self, writer: asyncio.StreamWriter, response: HttpResponse
    ):
        await self.response_writer.send(
            writer,
            {
                "type": "http.response.start",
                "status": response.status_code,
                "headers": [
                    (k.encode(), v.encode()) for k, v in response.headers.items()
                ],
            },
        )
        await self.response_writer.send(
            writer,
            {"type": "http.response.body", "body": response.body, "more_body": False},
        )

    async def _close_connection(
        self, writer: asyncio.StreamWriter, client_addr: tuple[str, int]
    ) -> None:
        logger.debug(f"Closing connection from {client_addr}")
        writer.close()
        await writer.wait_closed()
        logger.info(f"Connection from {client_addr} closed")

    async def start(self) -> None:
        server = await asyncio.start_server(
            self.handle_connection, self.host, self.port, ssl=self.ssl_context
        )

        protocol = "https" if self.ssl_context else "http"
        logger.info(f"Nimbus server running on {protocol}://{self.host}:{self.port}")

        async with server:
            await server.serve_forever()

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            logger.info("Server stopped.")
