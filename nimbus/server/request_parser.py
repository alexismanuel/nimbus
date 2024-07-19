import asyncio
from typing import List, Tuple
from urllib.parse import urlparse

from nimbus.types import Scope


class RequestParser:
    async def parse_request(
        self, reader: asyncio.StreamReader
    ) -> Tuple[str, str, List[Tuple[bytes, bytes]]]:
        request_line = await reader.readline()
        method, path, _ = request_line.decode().strip().split()
        headers = await self._parse_headers(reader)
        return method, path, headers

    async def _parse_headers(
        self, reader: asyncio.StreamReader
    ) -> List[Tuple[bytes, bytes]]:
        headers = []
        while True:
            line = await reader.readline()
            if line == b"\r\n":
                break
            name, value = line.decode().strip().split(": ", 1)
            headers.append((name.lower().encode(), value.encode()))
        return headers

    def create_scope(
        self,
        method: str,
        path: str,
        headers: List[Tuple[bytes, bytes]],
        server: Tuple[str, int],
        client: Tuple[str, int],
    ) -> Scope:
        parsed_url = urlparse(path)
        return {
            "type": "http",
            "asgi": {"version": "3.0", "spec_version": "2.1"},
            "http_version": "1.1",
            "method": method,
            "path": parsed_url.path,
            "raw_path": parsed_url.path.encode(),
            "query_string": parsed_url.query.encode(),
            "headers": headers,
            "server": server,
            "client": client,
        }
