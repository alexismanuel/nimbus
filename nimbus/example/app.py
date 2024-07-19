import json
import logging
import time

from nimbus.applications import NimbusApp
from nimbus.connections import HttpConnection, WebSocketConnection
from nimbus.example.routers import admin_router, api_router
from nimbus.response import HttpResponse

logger = logging.getLogger(__name__)

app = NimbusApp()


async def timing_middleware(connection: HttpConnection, next_middleware):
    start_time = time.time()
    response = await next_middleware()
    end_time = time.time()
    logger.debug(
        f"Request to {connection.scope['path']} took {end_time - start_time:.4f} seconds"
    )
    return response


app.add_middleware(timing_middleware)

app.mount("/api", api_router)
app.mount("/admin", admin_router)


@app.route("/")
async def index(connection: HttpConnection):
    return HttpResponse("Welcome to the modular Nimbus app!")


@app.websocket("/ws")
async def websocket_endpoint(connection: WebSocketConnection):
    await connection.accept()
    try:
        while True:
            message = await connection.receive_message()
            if message is None:
                break
            response = json.dumps({"echo": message})
            await connection.send_message(response)
    finally:
        await connection.close()
