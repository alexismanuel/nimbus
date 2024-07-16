from nimbus.router import Router
from nimbus.connection import Connection
from nimbus.response import HttpResponse, JsonResponse
from urllib.parse import parse_qs

router = Router()

@router.route('/')
async def index(connection: Connection):
    await HttpResponse("Welcome to the Greeting App!", connection)

@router.route('/greet/<name>')
async def greet(connection: Connection, name: str):
    format = parse_qs(connection.scope['query_string'].decode()).get('format', ['text'])[0]
    greeting = f"Hello, {name}!"
    
    if format == 'json':
        await JsonResponse({'greeting': greeting}, connection)
    else:
        await HttpResponse(greeting, connection)

@router.route('/api/greet', methods=['POST'])
async def api_greet(connection: Connection):
    body = await connection.get_body()
    data = parse_qs(body.decode())
    name = data.get('name', ['World'])[0]
    await JsonResponse({'greeting': f"Hello, {name}!"}, connection)

# Use the router as the main application
app = router