from functools import cached_property
from http.cookies import SimpleCookie
from typing import Dict, Callable, Any, Optional, Union, AsyncIterator
from urllib.parse import parse_qsl

from nimbus.types import ConnectionType
from nimbus.exceptions import ResponseAlreadyStarted

class Connection:
    def __init__(self, scope: Dict[str, Any], receive: Callable, send: Callable):
        self.scope = scope
        self.receive = receive
        self._raw_send = send
        self.type = ConnectionType.WebSocket if scope['type'] == 'websocket' else ConnectionType.HTTP
        self.started = False
        self.finished = False
        self.response_headers: Dict[bytes, bytes] = {}
        self.response_status: int = 200

    @cached_property
    def headers(self) -> Dict[str, str]:
        return {k.decode('ascii'): v.decode('ascii') for k, v in self.scope['headers']}

    @cached_property
    def cookies(self) -> SimpleCookie:
        cookie = SimpleCookie()
        cookie.load(self.headers.get('cookie', ''))
        return cookie

    @cached_property
    def query_params(self) -> Dict[str, str]:
        return dict(parse_qsl(self.scope['query_string'].decode()))

    async def get_body(self) -> bytes:
        body = b''
        more_body = True
        while more_body:
            message = await self.receive()
            body += message.get('body', b'')
            more_body = message.get('more_body', False)
        return body

    async def send(self, event: Dict[str, Any]):
        await self._raw_send(event)

    async def send_response(self, status: int, body: Union[str, bytes], headers: Optional[Dict[str, str]] = None):
        if self.started:
            raise ResponseAlreadyStarted("Response already started")
        self.started = True
        if headers:
            self.response_headers.update({k.encode('ascii'): v.encode('ascii') for k, v in headers.items()})
        await self.send({
            'type': 'http.response.start',
            'status': status,
            'headers': list(self.response_headers.items()),
        })
        if isinstance(body, str):
            body = body.encode('utf-8')
        await self.send({
            'type': 'http.response.body',
            'body': body,
            'more_body': False
        })
        self.finished = True

    async def stream_response(self, status: int, body_iterator: AsyncIterator[Union[str, bytes]], headers: Optional[Dict[str, str]] = None):
        if self.started:
            raise ResponseAlreadyStarted("Response already started")
        self.started = True
        self.response_status = status
        if headers:
            self.response_headers.update({k.encode('ascii'): v.encode('ascii') for k, v in headers.items()})
        await self.send({
            'type': 'http.response.start',
            'status': status,
            'headers': list(self.response_headers.items()),
        })
        async for chunk in body_iterator:
            if isinstance(chunk, str):
                chunk = chunk.encode('utf-8')
            await self.send({
                'type': 'http.response.body',
                'body': chunk,
                'more_body': True,
            })
        await self.send({
            'type': 'http.response.body',
            'body': b'',
            'more_body': False,
        })
        self.finished = True