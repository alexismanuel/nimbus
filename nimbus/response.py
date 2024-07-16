import json
from typing import Union, Optional, Mapping, Any

from nimbus.connection import Connection


class HttpResponse:
    def __init__(
        self,
        body: Optional[Union[bytes, str]] = b"",
        connection: Optional[Connection] = None,
        *,
        status_code: int = 200,
        headers: Optional[Mapping[str, str]] = None
    ):
        self.body = body
        self.connection = connection
        self.status_code = status_code
        self.headers = headers

    def __await__(self):
        if not self.connection:
            raise ValueError("No connection")
        return self.connection.send_response(self.status_code, self.body, self.headers).__await__()


class JsonResponse(HttpResponse):
    def __init__(
        self, data: Any, connection: Optional[Connection] = None, *args, **kwargs
    ):
        body = json.dumps(data)
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        headers["content-type"] = "application/json"
        kwargs["headers"] = headers
        super().__init__(body, connection, *args, **kwargs)
