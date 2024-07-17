import time
import logging

from nimbus.applications import NimbusApp
from nimbus.example.routers import api_router, admin_router
from nimbus.response import HttpResponse
from nimbus.connection import Connection


logger = logging.getLogger(__name__)

app = NimbusApp()

async def timing_middleware(connection: Connection, next_middleware):
    start_time = time.time()
    response = await next_middleware()
    end_time = time.time()
    logger.debug(f"Request to {connection.scope['path']} took {end_time - start_time:.4f} seconds")
    return response

# Add middleware to the app
app.add_middleware(timing_middleware)

@app.route('/')
async def index(connection: Connection):
    return HttpResponse("Welcome to the modular Nimbus app!")

app.mount('/api', api_router)
app.mount('/admin', admin_router)
