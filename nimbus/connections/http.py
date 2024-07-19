from typing import AsyncIterator, Dict, Optional, Union, Any

from nimbus.exceptions import ResponseAlreadyStarted
from nimbus.types import ReceiveCallable, Scope, SendCallable
from nimbus.server.body_parser import BodyParser

from nimbus.connections.base import BaseConnection


class HttpConnection(BaseConnection):
    def __init__(self, scope: Scope, receive: ReceiveCallable, send: SendCallable):
        super().__init__(scope, receive, send)
        self.started = False
        self.finished = False
        self.response_headers: Dict[bytes, bytes] = {}
        self.response_status: int = 200
        self._body = None
        self._parsed_body = None

    async def get_body(self) -> bytes:
        if self._body is None:
            content_length = int(self.headers.get("content-length", "0"))
            self._body = await self.receive(content_length)
        return self._body

    async def get_parsed_body(self) -> Optional[Dict[str, Any]]:
        if self._parsed_body is None:
            body = await self.get_body()
            self._parsed_body = await BodyParser.parse(self.headers, body)
        return self._parsed_body

    async def send_response(
        self,
        status: int,
        body: Union[str, bytes],
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._ensure_response_not_started()
        self._prepare_response(status, headers)
        await self._send_response_start()
        await self._send_response_body(body)
        self.finished = True

    def _ensure_response_not_started(self) -> None:
        if self.started:
            raise ResponseAlreadyStarted("Response already started")
        self.started = True

    def _prepare_response(self, status: int, headers: Optional[Dict[str, str]]) -> None:
        self.response_status = status
        if headers:
            self.response_headers.update(
                {k.encode("ascii"): v.encode("ascii") for k, v in headers.items()}
            )

    async def _send_response_start(self) -> None:
        await self.send(
            {
                "type": "http.response.start",
                "status": self.response_status,
                "headers": list(self.response_headers.items()),
            }
        )

    async def _send_response_body(self, body: Union[str, bytes]) -> None:
        if isinstance(body, str):
            body = body.encode("utf-8")
        await self.send(
            {"type": "http.response.body", "body": body, "more_body": False}
        )

    async def stream_response(
        self,
        status: int,
        body_iterator: AsyncIterator[Union[str, bytes]],
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        self._ensure_response_not_started()
        self._prepare_response(status, headers)
        await self._send_response_start()
        await self._stream_response_body(body_iterator)
        self.finished = True

    async def _stream_response_body(
        self, body_iterator: AsyncIterator[Union[str, bytes]]
    ) -> None:
        async for chunk in body_iterator:
            await self._send_response_chunk(chunk, more_body=True)
        await self._send_response_chunk(b"", more_body=False)

    async def _send_response_chunk(
        self, chunk: Union[str, bytes], more_body: bool
    ) -> None:
        if isinstance(chunk, str):
            chunk = chunk.encode("utf-8")
        await self.send(
            {
                "type": "http.response.body",
                "body": chunk,
                "more_body": more_body,
            }
        )
