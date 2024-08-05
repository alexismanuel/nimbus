from functools import cached_property
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import parse_qsl

from nimbus.types import ReceiveCallable, Scope, SendCallable


class BaseConnection:
    def __init__(self, scope: Scope, receive: ReceiveCallable, send: SendCallable):
        self.scope = scope
        self.receive = receive
        self._raw_send = send

    @cached_property
    def headers(self) -> dict[str, str]:
        return {k.decode("ascii"): v.decode("ascii") for k, v in self.scope["headers"]}

    @cached_property
    def cookies(self) -> SimpleCookie:
        cookie = SimpleCookie()
        cookie.load(self.headers.get("cookie", ""))
        return cookie

    @cached_property
    def query_params(self) -> dict[str, str]:
        return dict(parse_qsl(self.scope["query_string"].decode()))

    async def send(self, event: dict[str, Any]) -> None:
        await self._raw_send(event)
