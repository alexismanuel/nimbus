# Nimbus ASGI Server

Nimbus is a lightweight, extensible ASGI (Asynchronous Server Gateway Interface) server implemented in Python. It provides a simple yet powerful foundation for building asynchronous web applications and APIs.

## Features

- **ASGI Compliant**: Fully compliant with the ASGI 3.0 specification.
- **Asynchronous**: Built on Python's asyncio for high performance.
- **Simple API**: Easy-to-use API for creating ASGI applications.
- **Extensible**: Designed with extensibility in mind for easy addition of middleware and plugins.
- **Logging**: Comprehensive logging for debugging and monitoring.
- **Connection Handling**: Efficient handling of HTTP connections.

## Installation

To install Nimbus, you can use pip:

```bash
pip install nimbus-asgi # replace with final package name
```

Note: Not yet published !

## Quick Start

Here's a simple example of how to use Nimbus:

```python
from nimbus.applications import NimbusApp
from nimbus.server import NimbusServer

class MyApp(NimbusApp):
    async def __call__(self, connection):
        await connection.send_response(200, 'Hello, World!', {'Content-Type': 'text/plain'})

if __name__ == "__main__":
    app = MyApp()
    NimbusServer(app).run()
```

This will start a server on `http://localhost:8000` that responds with "Hello, World!" to all requests.

## Usage

### Creating an Application

To create a Nimbus application, subclass `NimbusApp`:

```python
from nimbus.applications import NimbusApp

class MyApp(NimbusApp):
    async def __call__(self, connection):
        # Your application logic here
        await connection.send_response(200, 'Hello from MyApp!', {'Content-Type': 'text/plain'})
```

### Running the Server

To run the server with your application:

```python
from nimbus.server import NimbusServer
from myapp import MyApp

if __name__ == "__main__":
    app = MyApp()
    server = NimbusServer(app, host='0.0.0.0', port=8080)
    server.run()
```

## Configuration

Nimbus server can be configured with the following parameters:

- `host`: The host to bind the server to (default: '127.0.0.1')
- `port`: The port to bind the server to (default: 8000)
- `ssl_keyfile`: Path to SSL key file for HTTPS support
- `ssl_certfile`: Path to SSL certificate file for HTTPS support

## Future Enhancements

- WebSocket support
- Middleware support
- Request routing
- Static file serving
- Request body parsing for different content types
- HTTPS support with autocert
- Performance optimizations

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- Inspired by other ASGI servers like Uvicorn and Hypercorn.
- Built with Python's asyncio library.
