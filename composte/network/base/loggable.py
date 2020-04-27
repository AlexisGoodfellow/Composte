"""Define loggable interface."""
import logging
import sys

from composte.network.base import exceptions


class IsNone(exceptions.GenericError):
    """Thrown when logger is None."""

    pass


class Loggable:
    """Base class to provide logging facilities."""

    def __init__(self, logger):
        """Initialize the logger."""
        if logger is None:
            raise IsNone("Logger must not be None")
        self.__logger = logger

    def info(self, message: str):
        """Log information."""
        self.__logger.info(message)

    def debug(self, message: str):
        """Log debug message."""
        self.__logger.debug(message)

    def warn(self, message: str):
        """Log warning."""
        self.__logger.warn(message)

    def error(self, message: str):
        """Log error."""
        self.__logger.error(message)

    def critical(self, message: str):
        """Log critical issue."""
        self.__logger.critical(message)


class devnull(Loggable):
    """Sometimes you don't care what they have to say."""

    def __init__(self, logger=None):
        """Do nothing."""
        pass

    def info(self, message: str):
        """Log nothing."""
        pass

    def debug(self, message: str):
        """Log nothing."""
        pass

    def warn(self, message: str):
        """Log nothing."""
        pass

    def error(self, message: str):
        """Log nothing."""
        pass

    def critical(self, message: str):
        """Log nothing."""
        pass


DevNull = devnull()


class AdHoc:
    """
    Ad-Hoc logger for Loggable. Provide your own sink that supports write().

    Usually an open file or sys.stderr.
    Does not do formatting, etc
    """

    def __init__(self, sink, loglevel=logging.DEBUG, name=None, **kwargs):
        """
        Use kwargs to provide prefixes for custom loglevels.

        The following are provided by default:
            INFO
            DEBUG
            WARNING
            ERROR
            CRITICAL
        Prefixes default to the names of the loglevels
        The logger name is provided alongside all messages
        """
        self.__sink = sink
        self.__level = loglevel
        self.__name = f"{name}/" if name else ""

        self.__prefixes = {
            f"info": "[{self.__name}INFO]: ",
            f"debug": "[{self.__name}DEBUG]: ",
            f"warning": "[{self.__name}WARNING]: ",
            f"error": "[{self.__name}ERROR]: ",
            f"critical": "[{self.__name}CRITICAL]: ",
        }
        self.__prefixes.update(kwargs)

    def __log(self, message: str, level):
        """Write the log message."""
        message = str(message)
        if self.__level <= level:
            self.__sink.write(message + "\n")

    def info(self, message: str):
        """Log information."""
        self.__log(self.__prefixes["info"] + str(message), logging.INFO)

    def debug(self, message: str):
        """Log debug message."""
        self.__log(self.__prefixes["debug"] + str(message), logging.DEBUG)

    def warn(self, message: str):
        """Log warning."""
        self.__log(self.__prefixes["warn"] + str(message), logging.WARNING)

    def error(self, message: str):
        """Log error."""
        self.__log(self.__prefixes["error"] + str(message), logging.ERROR)

    def critical(self, message: str):
        """Log critical issue."""
        self.__log(self.__prefixes["critical"] + str(message), logging.CRITICAL)


StdErr = AdHoc(sys.stderr, name="stderr")


class Combined:
    """Combine loggers to duplicate logging statements to multiple sinks."""

    def __init__(self, loggers):
        """Initialize multiple loggers."""
        self.__loggers = []

        try:
            for logger in loggers:
                self.__loggers.append(logger)
        except TypeError:
            self.__loggers.append(loggers)

    def add(self, logger):
        """Add a logger."""
        self.__logger.append(logger)

    def remove(self, logger):
        """Remove a logger."""
        try:
            self.__loggers.remove(logger)
        except ValueError:
            pass

    def info(self, message: str):
        """Log information."""
        for logger in self.__loggers:
            logger.info(message)

    def debug(self, message: str):
        """Log debug message."""
        for logger in self.__loggers:
            logger.debug(message)

    def warn(self, message: str):
        """Log warning."""
        for logger in self.__loggers:
            logger.warn(message)

    def error(self, message: str):
        """Log error."""
        for logger in self.__loggers:
            logger.error(message)

    def critical(self, message: str):
        """Log critical issue."""
        for logger in self.__loggers:
            logger.critical(message)
