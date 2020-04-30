#!/usr/bin/env python3
"""Composte network server."""

import logging
import signal  # Need signal handlers to properly run as daemon
import sys
import traceback
from threading import Lock, Thread
from typing import Callable, Optional

import zmq

from composte.network.base.exceptions import DecryptError, EncryptError, GenericError
from composte.network.base.loggable import Loggable
from composte.network.conf import logging as log
from composte.network.fake.security import Encryption, Log

DEBUG = False


class Server(Loggable):
    """
    The network server for composte.

    Broadcast socket   -> Publish/Subscribe
    Interactive socket -> Request/Reply

    A REP socket replies to the client who sent the last message. This means
    that we can't really get away with worker threads here, as
    REQ/Processing/REP must be serialized as a cohesive unit. This problem seems
    to be generally tractable though, per
    https://stackoverflow.com/questions/29420666/zmq-multiple-request-reply-pairs
    """

    __context = zmq.Context()

    def __init__(
        self,
        interactive_address,
        broadcast_address,
        logger,
        encryption_scheme=Encryption(),
    ):
        """
        Initialize the network server for Composte.

        interactive_address and broadcast_address must be available for this
        application to bind to.
        encryption_scheme must provide encrypt and decrypt methods
        logger must support at least the methods of base.loggable.Loggable
        """
        super(Server, self).__init__(logger)

        self.__translator = encryption_scheme

        self.__iaddr = interactive_address
        self.__isocket = self.__context.socket(zmq.REP)
        self.__isocket.bind(self.__iaddr)

        self.__baddr = broadcast_address
        self.__bsocket = self.__context.socket(zmq.PUB)
        self.__bsocket.bind(self.__baddr)

        self.__dlock = Lock()
        self.__done = False

        self.__ilock = Lock()
        self.__block = Lock()

        self.__listen_thread = None

    def broadcast(self, message):
        """Broadcast a message to all subscribed clients."""
        self.info(f"Broadcasting {message}")
        with self.__block:
            self.__bsocket.send_string(message)

    def fail(self, message, reason):
        """Send a failure message to a client."""
        # Probably need a better generic failure message format, but eh
        self.error(f"Failure ({message}): {reason}")
        self.__isocket.send_string(f"Failure ({reason}): {message}")

    def start_background(
        self,
        handler: Callable = lambda x: x,
        preprocess: Callable = lambda x: x,
        postprocess: Callable = lambda msg: msg,
        poll_timeout: int = 2000,
    ):
        """Start Server.__listen_almost_forever in the background."""
        if self.__listen_thread is not None:
            return
        self.__listen_thread = Thread(
            target=self.__listen_almost_forever,
            args=(handler, preprocess, postprocess, poll_timeout),
        )
        self.__listen_thread.start()

    def __message_handling_flow(
        self,
        message: str,
        handler: Callable = lambda x: x,
        preprocess: Callable = lambda x: x,
        postprocess: Callable = lambda msg: msg,
    ) -> Optional[str]:
        try:
            message = self.__translator.decrypt(message)
        except DecryptError:
            self.fail(message, "Decryption failure")
            return None

        try:
            message = preprocess(message)
            reply = handler(self, message)
            reply = postprocess(reply)
        except GenericError:
            self.fail(message, "Internal server error")
            return None

        try:
            reply = self.__translator.encrypt(reply)
        except EncryptError:
            self.fail(message, "Encryption failure")
            return None

        return reply

    def __create_reply(
        self,
        handler: Callable = lambda x: x,
        preprocess: Callable = lambda x: x,
        postprocess: Callable = lambda msg: msg,
    ):
        message = self.__isocket.recv_string()
        # Unconditionally catch and ignore _all_ unexpected
        # exceptions during the invocations of client-provided
        # functions
        try:
            reply = self.__message_handling_flow(
                message, handler, preprocess, postprocess
            )
            if reply:
                self.__isocket.send_string(reply)
            else:
                self.fail(message, "Malformed message")
        except Exception:
            self.fail(message, "Malformed message")
            self.error(f"Uncaught exception: {traceback.format_exc()}")

    def __listen_almost_forever(
        self,
        handler: Callable = lambda x: x,
        preprocess: Callable = lambda x: x,
        postprocess: Callable = lambda msg: msg,
        poll_timeout: int = 2000,
    ):
        """
        Poll for messages on the interactive socket until the server is stopped.

        poll_timeout controls how long a poll operation will wait before failing.
        Messages are pushed through the pipeline preprocess -> handler ->
        postprocess, and the result is sent back to as a client
        """
        try:
            while True:
                with self.__dlock:
                    if self.__done:
                        break

                with self.__ilock:
                    nmsg = self.__isocket.poll(poll_timeout)
                    if nmsg != 0:
                        self.__create_reply(handler, preprocess, postprocess)

        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Stop the server."""
        self.info("Shutting down server")
        with self.__dlock:
            self.info("Stopping polling")
            self.__done = True

        with self.__ilock:
            iaddr = self.__isocket.last_endpoint.decode()
            self.info(f"Unbinding interactive socket from {iaddr}")
            self.__isocket.unbind(iaddr)

        with self.__block:
            baddr = self.__bsocket.last_endpoint.decode()
            self.info("Unbinding broadcast socket from {}".format(baddr))
            self.__bsocket.unbind(baddr)

        self.__listen_thread.join()

        self.info("Server stopped")


def echo(server, message):
    """Echo the message back to the client a la bash."""
    server.info("Echoing {message}")
    server.broadcast(message)
    return message


def stop_server(sig, frame, server):
    """Stop the server."""
    server.stop()


if __name__ == "__main__":

    log.setup()

    logging.getLogger(__name__).info("Hello yes this is a test")

    # Set up the server
    s = Server(
        "tcp://127.0.0.1:5000",
        "tcp://127.0.0.1:6667",
        logging.getLogger("server"),
        Log(sys.stderr),
    )

    if not DEBUG:
        signal.signal(signal.SIGINT, lambda sig, f: stop_server(sig, f, s))
        signal.signal(signal.SIGQUIT, lambda sig, f: stop_server(sig, f, s))
        signal.signal(signal.SIGTERM, lambda sig, f: stop_server(sig, f, s))

    # Start listening
    s.start_background(echo)
