"""Setup logging configuration."""
import logging
import logging.config
import os


def setup():
    """Set up logging configs based on a logging config file."""
    try:
        os.mkdir("logs")
    except FileExistsError:
        pass

    logging.config.fileConfig(os.path.join(os.path.dirname(__file__), "logging.conf"))
