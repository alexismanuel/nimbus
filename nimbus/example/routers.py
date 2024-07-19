from nimbus.connections import HttpConnection
from nimbus.response import HttpResponse, JsonResponse
from nimbus.router import Router

api_router = Router()


@api_router.get("/hello/<name>")
async def hello(connection: HttpConnection, name: str):
    return JsonResponse({"message": f"Hello, {name}!"})


@api_router.post("/echo")
async def echo(connection: HttpConnection):
    body = await connection.get_body()
    return JsonResponse({"echoed": body.decode()})


admin_router = Router()


@admin_router.get("/dashboard")
async def admin_dashboard(connection: HttpConnection):
    return HttpResponse("Admin Dashboard")
