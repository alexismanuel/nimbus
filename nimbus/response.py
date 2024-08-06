import json
from typing import Any, Optional, Union

from nimbus.connections import HttpConnection


class HttpResponse:
    def __init__(
        self,
        body: Union[bytes, str] = b"",
        connection: Optional[HttpConnection] = None,
        *,
        status_code: int = 200,
        headers: dict[str, str] = {},
    ):
        self.body = body
        self.connection = connection
        self.status_code = status_code
        self.headers = headers

    def __await__(self):
        if not self.connection:
            raise ValueError("No connection")
        return self.connection.send_response(
            self.status_code, self.body, self.headers
        ).__await__()


class JsonResponse(HttpResponse):
    def __init__(
        self, data: Any, connection: Optional[HttpConnection] = None, *args, **kwargs
    ):
        body = json.dumps(data)
        headers = kwargs.get("headers")
        if headers is None:
            headers = {}
        headers["content-type"] = "application/json"
        kwargs["headers"] = headers
        super().__init__(body, connection, *args, **kwargs)
