"""Encryption related functions."""


class Encryption:
    """
    The minimum interface that network encryption_scheme must implement.

    Note that this particular implementation doesn't do anything.
    """

    def __init__(self):
        """Initialize the encryption protocol."""
        pass

    def encrypt(self, message: str):
        """Encrypt message before it goes out."""
        return message

    def decrypt(self, message: str):
        """Decrypt message before trying to read it."""
        return message


class Log:
    """Sample class that logs to a write()-able sink."""

    def __init__(self, sink):
        """Initialize the logger with its logging location."""
        self.__sink = sink

    def log(self, message: str) -> str:
        """Log to the sink."""
        self.__sink.write(f"Logging: {message}\n")
        self.__sink.flush()
        return message

    def encrypt(self, message: str) -> str:
        """Encrypt logs before they hit the sink."""
        return self.log(message)

    def decrypt(self, message: str) -> str:
        """Decrypt logs when fetching from the sink."""
        return self.log(message)
