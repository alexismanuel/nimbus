import logging

from nimbus.example.app import app
from nimbus.server.server import NimbusServer

logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    NimbusServer(app).run()
