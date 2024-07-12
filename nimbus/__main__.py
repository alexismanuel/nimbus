from nimbus.example import app
from nimbus.server import NimbusServer
import logging


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    NimbusServer(app).run()
