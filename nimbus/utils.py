import ssl
from typing import Optional

def create_ssl_context(keyfile: Optional[str], certfile: Optional[str]) -> Optional[ssl.SSLContext]:
    if keyfile and certfile:
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(certfile=certfile, keyfile=keyfile)
        return ssl_context
    return None