import pytest
from typing import Dict, Any, Optional, List, Union
from unittest.mock import Mock, AsyncMock
from nimbus.applications import ASGIApplication, NimbusApp
from nimbus.connections import HttpConnection, WebSocketConnection
from nimbus.response import HttpResponse
from nimbus.router import Router

class MockHttpConnection(HttpConnection):
    def __init__(self, scope: Dict[str, Any]):
        super().__init__(scope, AsyncMock(), AsyncMock())
        self.started = False
        self.finished = False
        self.response_headers: Dict[bytes, bytes] = {}
        self.response_status: int = 200
        self._body = b""
        self._parsed_body = None
        self.sent_messages = []

    async def get_body(self) -> bytes:
        return self._body

    async def get_parsed_body(self) -> Optional[Dict[str, Any]]:
        return self._parsed_body

    async def send_response(
        self,
        status: int,
        body: Union[str, bytes],
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        await super().send_response(status, body, headers)

    async def send(self, message: Dict[str, Any]) -> None:
        self.sent_messages.append(message)
        await super().send(message)

    def get_sent_messages(self) -> List[Dict[str, Any]]:
        return self.sent_messages

@pytest.fixture
def app():
    return NimbusApp()

class TestASGIApplicationCall:
    @pytest.mark.asyncio
    async def test_valid(self):
        class ConcreteASGI(ASGIApplication):
            async def __call__(self, scope, receive, send):
                pass

        app = ConcreteASGI()
        await app({}, lambda: None, lambda x: None)
    
    @pytest.mark.asyncio
    async def test_not_implemented(self):
        class NotSoConcreteASGI(ASGIApplication):
            pass
        with pytest.raises(TypeError):
            _ = NotSoConcreteASGI()

class TestInit:
    def test_valid(self, app: NimbusApp):
        assert isinstance(app, NimbusApp)
        assert isinstance(app.default_router, Router)
        assert app.routers == [('', app.default_router)]
    
    @pytest.mark.asyncio
    async def test_websocket_handler(self, app: NimbusApp):
        @app.websocket("/ws")
        async def handler(conn):
            await conn.send_message("Hello")

        assert "/ws" in app.websocket_handlers
        assert app.websocket_handlers["/ws"] == handler

class TestMount:
    def test_valid(self, app: NimbusApp):
        router = Router()
        app.mount("/test", router)
        assert ("/test", router) in app.routers
        assert router.prefix == "/test"

class TestAddMiddleware:
    def test_valid(self, app: NimbusApp):
        async def middleware(conn, next_middleware):
            return await next_middleware()
        
        app.add_middleware(middleware)
        assert middleware in app.middleware_manager.middlewares

class TestHandleWebsocket:
    @pytest.mark.asyncio
    async def test_valid(self, app: NimbusApp):
        mock_connection = Mock(spec=WebSocketConnection)
        mock_connection.scope = {"path": "/ws"}
        
        @app.websocket("/ws")
        async def handler(conn: WebSocketConnection):
            await conn.send_message("Hello")

        await app._handle_websocket(mock_connection)
        mock_connection.send_message.assert_called_once_with("Hello")
    
    @pytest.mark.asyncio
    async def test_no_handler(self, app: NimbusApp):
        mock_connection = Mock(spec=WebSocketConnection)
        mock_connection.scope = {"path": "/special_ws"}
        
        @app.websocket("/ws")
        async def handler(conn: WebSocketConnection):
            await conn.send_message("Hello")

        await app._handle_websocket(mock_connection)
        mock_connection.close.assert_called_once()

class TestHandleHttp:
    @pytest.mark.asyncio
    async def test_valid(self, app: NimbusApp):
        mock_connection = MockHttpConnection({
            "path": "/",
            "method": "GET",
            "headers": []
        })
        
        @app.get("/")
        async def index(conn):
            return HttpResponse("Hello")

        response = await app._handle_http(mock_connection)
        assert isinstance(response, HttpResponse)
        assert response.body == "Hello"
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_not_found(self, app: NimbusApp):
        mock_connection = MockHttpConnection({
            "path": "/hello",
            "method": "GET",
            "headers": []
        })
        
        @app.get("/")
        async def index(conn):
            return HttpResponse("Hello")

        response = await app._handle_http(mock_connection)
        assert isinstance(response, HttpResponse)
        assert response.body == "Not Found"
        assert response.status_code == 404

class TestCall:
    @pytest.mark.asyncio
    async def test_http(self, app: NimbusApp):
        mock_connection = MockHttpConnection({
            "path": "/",
            "method": "GET",
            "headers": []
        })
        
        @app.get("/")
        async def index(conn):
            return HttpResponse("Hello")

        response = await app(mock_connection)
        assert isinstance(response, HttpResponse)
        assert response.body == "Hello"

    @pytest.mark.asyncio
    async def test_websocket(self, app: NimbusApp):
        mock_connection = Mock(spec=WebSocketConnection)
        mock_connection.scope = {"path": "/ws"}
        
        @app.websocket("/ws")
        async def handler(conn):
            await conn.send_message("Hello")

        await app(mock_connection)
        mock_connection.send_message.assert_called_once_with("Hello")

class TestProcessHttpResponse:
    @pytest.mark.asyncio
    async def test_valid(self, app: NimbusApp):
        mock_connection = MockHttpConnection({
            "path": "/",
            "method": "GET",
            "headers": []
        })
        response = HttpResponse("Test Body", status_code=200, headers={"Content-Type": "text/plain"})
        processed_response = await app._process_http_response(response, mock_connection)
        assert processed_response == response
        assert processed_response.connection == mock_connection

class TestRoute:
    def test_valid(self, app: NimbusApp):
        @app.route("/test", methods=["GET", "POST"])
        async def test_route(conn):
            pass


        assert "/test" in [rule.rule for rule in app.default_router.url_map.iter_rules()]

class TestGet:  
    def test_valid(self, app: NimbusApp):
        @app.get("/get")
        async def get_route(conn):
            pass


        assert "/get" in [rule.rule for rule in app.default_router.url_map.iter_rules()]

class TestPost:
    def test_valid(self, app: NimbusApp):
        @app.post("/post")
        async def post_route(conn):
            pass

        assert "/post" in [rule.rule for rule in app.default_router.url_map.iter_rules()]

class TestPatch:
    def test_valid(self, app: NimbusApp):
        @app.patch("/patch")
        async def patch_route(conn):
            pass

        assert "/patch" in [rule.rule for rule in app.default_router.url_map.iter_rules()]
