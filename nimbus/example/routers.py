from nimbus.router import Router
from nimbus.response import HttpResponse, JsonResponse
from nimbus.connection import Connection


api_router = Router()

@api_router.get('/hello/<name>')
async def hello(connection: Connection, name: str):
    return JsonResponse({'message': f'Hello, {name}!'})

@api_router.post('/echo')
async def echo(connection: Connection):
    body = await connection.get_body()
    return JsonResponse({'echoed': body.decode()})


admin_router = Router()

@admin_router.get('/dashboard')
async def admin_dashboard(connection: Connection):
    return HttpResponse("Admin Dashboard")
