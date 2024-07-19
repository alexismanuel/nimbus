class NimbusException(Exception):
    """Base exception for Nimbus ASGI server."""


class ResponseAlreadyStarted(NimbusException):
    """Exception raised when attempting to start a response that has already been started."""


class UnsupportedConnectionType(ValueError):
    pass
