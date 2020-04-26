class Encryption:
    """
    Filler class defining the minimum interface that network encryption_scheme
    must implement.

    Note that this particular one doesn't do anything.
    """

    def __init__(self):
        pass

    def encrypt(self, message):
        return message

    def decrypt(self, message):
        return message


class Log:
    """Sample class that logs to a write()-able sink."""
    def __init__(self, sink):
        self.__sink = sink

    def log(self, message):
        self.__sink.write("Logging: " + str(message) + "\n")
        self.__sink.flush()
        return message

    def encrypt(self, message):
        return self.log(message)

    def decrypt(self, message):
        return self.log(message)
