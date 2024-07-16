from nimbus.applications import NimbusApp
from nimbus.example.routers import api_router, admin_router
from nimbus.response import HttpResponse
from nimbus.connection import Connection

app = NimbusApp()

@app.route('/')
async def index(connection: Connection):
    return HttpResponse("Welcome to the modular Nimbus app!")

app.mount('/api', api_router)
app.mount('/admin', admin_router)
