# nimbus
handcrafted asgi toolkit, sky's the limit ☁️

Nimbus is a lightweight, extensible ASGI (Asynchronous Server Gateway Interface) toolkit implemented in Python. It provides a simple yet powerful foundation for building asynchronous web applications and APIs.


## Features

- ASGI-compliant server implementation
- Modular design with support for mounting multiple applications
- Built-in routing system with support for HTTP methods and URL parameters
- Easy-to-use API for handling requests and sending responses
- SSL support for secure connections

## Quick Start

Here's a simple example of how to create and run a Nimbus application:

```python
from nimbus.applications import NimbusApp
from nimbus.server import NimbusServer
from nimbus.response import HttpResponse

app = NimbusApp()

@app.route('/')
async def hello(connection):
    return HttpResponse("Hello, World!")

if __name__ == "__main__":
    NimbusServer(app).run()
```

## Modular Application Structure

Nimbus supports a modular application structure. You can create multiple routers and mount them to different URL prefixes:

```python
from nimbus.applications import NimbusApp
from nimbus.router import Router
from nimbus.response import HttpResponse, JsonResponse

app = NimbusApp()
api_router = Router()
admin_router = Router()

@app.route('/')
async def index(connection):
    return HttpResponse("Welcome to the modular Nimbus app!")

@api_router.get('/hello/<name>')
async def hello(connection, name):
    return JsonResponse({'message': f'Hello, {name}!'})

@admin_router.get('/dashboard')
async def admin_dashboard(connection):
    return HttpResponse("Admin Dashboard")

app.mount('/api', api_router)
app.mount('/admin', admin_router)
```

## Running the Server

To run the Nimbus server:

```python
from nimbus.server import NimbusServer
from your_app import app

if __name__ == "__main__":
    NimbusServer(app).run()
```

## SSL Support

To enable SSL, provide the paths to your SSL certificate and key files:

```python
NimbusServer(app, ssl_certfile='path/to/cert.pem', ssl_keyfile='path/to/key.pem').run()
```

## Contributing

Contributions to Nimbus are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.