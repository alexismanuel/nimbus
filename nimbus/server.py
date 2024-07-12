import asyncio
import logging
from typing import Optional, Dict, Any, List, Tuple

from nimbus.connection import Connection
from nimbus.applications import ASGIApplication
from nimbus.utils import create_ssl_context

logger = logging.getLogger(__name__)

class NimbusServer:
    def __init__(self, app: ASGIApplication, host: str = '127.0.0.1', port: int = 8000,
                 ssl_keyfile: Optional[str] = None, ssl_certfile: Optional[str] = None):
        self.app = app
        self.host = host
        self.port = port
        self.ssl_context = create_ssl_context(ssl_keyfile, ssl_certfile) if ssl_keyfile and ssl_certfile else None

    async def handle_connection(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        client_addr = writer.get_extra_info('peername')
        logger.info(f"New connection from {client_addr}")
        try:
            method, path, headers = await self.parse_request(reader)
            scope = self.create_scope(method, path, headers, client_addr)
            connection = Connection(scope, reader.read, self.create_send_function(writer))
            await self.process_request(connection)
        except asyncio.CancelledError:
            logger.info(f"Connection from {client_addr} cancelled")
        except asyncio.IncompleteReadError:
            logger.info(f"Client {client_addr} disconnected before sending complete request")
        except ConnectionResetError:
            logger.info(f"Connection reset by client {client_addr}")
        except Exception as e:
            logger.error(f"Error handling connection from {client_addr}: {str(e)}", exc_info=True)
        finally:
            await self.close_connection(writer)
            logger.info(f"Connection from {client_addr} closed")

    async def parse_request(self, reader: asyncio.StreamReader) -> Tuple[str, str, List[Tuple[bytes, bytes]]]:
        request_line = await reader.readline()
        method, path, _ = request_line.decode().strip().split()
        logger.debug(f"Received request: {method} {path}")
        
        headers = []
        while True:
            line = await reader.readline()
            if line == b'\r\n':
                break
            name, value = line.decode().strip().split(': ', 1)
            headers.append((name.lower().encode(), value.encode()))
        
        logger.debug(f"Received headers: {headers}")
        return method, path, headers

    def create_scope(self, method: str, path: str, headers: List[Tuple[bytes, bytes]], client_addr: Tuple[str, int]) -> Dict[str, Any]:
        return {
            'type': 'http',
            'asgi': {'version': '3.0', 'spec_version': '2.1'},
            'http_version': '1.1',
            'method': method,
            'path': path,
            'raw_path': path.encode(),
            'query_string': b'',
            'headers': headers,
            'server': (self.host, self.port),
            'client': client_addr,
        }

    def create_send_function(self, writer: asyncio.StreamWriter):
        async def send(event: Dict[str, Any]):
            if event['type'] == 'http.response.start':
                status = event['status']
                headers = event['headers']
                writer.write(f'HTTP/1.1 {status}\r\n'.encode())
                for name, value in headers:
                    writer.write(f'{name.decode("ascii")}: {value.decode("ascii")}\r\n'.encode())
                writer.write(b'\r\n')
                logger.debug(f"Started response: status {status}")
            elif event['type'] == 'http.response.body':
                writer.write(event['body'])
                if not event.get('more_body', False):
                    logger.debug("Completed sending response body")
            await writer.drain()
        return send

    async def process_request(self, connection: Connection):
        logger.debug("Calling ASGI application")
        await self.app(connection)
        
        if not connection.started:
            logger.warning("Application did not start response")
            await connection.send_response(500, b'Internal Server Error')
        
        if not connection.finished:
            logger.warning("Response was not completed")
            await connection.send({
                'type': 'http.response.body',
                'body': b'',
                'more_body': False
            })

    async def close_connection(self, writer: asyncio.StreamWriter):
        logger.debug("Closing writer")
        writer.close()
        await writer.wait_closed()

    async def start(self) -> None:
        server = await asyncio.start_server(
            self.handle_connection, self.host, self.port, ssl=self.ssl_context
        )
        
        protocol = 'https' if self.ssl_context else 'http'
        logger.info(f'Nimbus server running on {protocol}://{self.host}:{self.port}')
        
        async with server:
            await server.serve_forever()

    def run(self) -> None:
        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(self.start())
        except KeyboardInterrupt:
            logger.info('Server stopped.')