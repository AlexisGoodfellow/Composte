#!/usr/bin/env python3

import logging
# Need signal handlers to properly run as daemon
import signal
import sys
import traceback
from threading import Lock, Thread

import zmq

from network.base.exceptions import DecryptError, EncryptError, GenericError
from network.base.loggable import Loggable, StdErr
from network.conf import logging as log
from network.fake.security import Encryption, Log

# A REP socket replies to the client who sent the last message. This means
# that we can't really get away with worker threads here, as
# REQ/Processing/REP must be serialized as a cohesive unit. This problem seems
# to be generally tractable though, per
# https://stackoverflow.com/questions/29420666/zmq-multiple-request-reply-pairs




DEBUG = False

# Broadcast socket   -> Publish/Subscribe
# Interactive socket -> Request/Reply
class Server(Loggable):
    __context = zmq.Context()

    def __init__(
        self,
        interactive_address,
        broadcast_address,
        logger,
        encryption_scheme=Encryption(),
    ):
        """
        Server.__init__(self, interactive_address, broadcast_address,
            logger, encryption_scheme = Encryption(), logger = None)
        The network server for Composte.
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

        # self.info("Bound to {} and {}".format(self.__iaddr, self.__baddr))

    def broadcast(self, message):
        """
        Server.broadcast(self, message)
        Broadcast a message to all subscribed clients
        """
        self.info("Broadcasting {}".format(message))
        with self.__block:
            self.__bsocket.send_string(message)

    def fail(self, message, reason):
        """
        Server.fail(self, message, reason)
        Send a failure message to a client
        """
        # Probably need a better generic failure message format, but eh
        self.error("Failure ({}): {}".format(message, reason))
        self.__isocket.send_string("Failure ({}): {}".format(reason, message))

    def start_background(
        self,
        handler=lambda x: x,
        preprocess=lambda x: x,
        postprocess=lambda msg: msg,
        poll_timeout=2000,
    ):
        """
        Server.start_background
        Starts Server.__listen_almost_forever in a background thread,
        forwarding arguments. For further details, see
        Server.__listen_almost_forever
        """
        if self.__listen_thread != None:
            return
        self.__listen_thread = Thread(
            target=self.__listen_almost_forever,
            args=(handler, preprocess, postprocess, poll_timeout),
        )
        self.__listen_thread.start()

    def __listen_almost_forever(
        self,
        handler=lambda x: x,
        preprocess=lambda x: x,
        postprocess=lambda msg: msg,
        poll_timeout=2000,
    ):
        """
        Server.__listen_almost_forever(self, handler = lambda msg: msg,
            preprocess = lambda msg: msg, poll_timeout = 2000)
        Polls for messages on the interactive socket until the server is
        stopped. poll_timeout controls how long a poll operation will wait
        before failing.
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
                    if nmsg == 0:
                        continue
                    message = self.__isocket.recv_string()
                    # Unconditionally catch and ignore _all_ unexpected
                    # exceptions during the invocations of client-provided
                    # functions
                    try:
                        try:
                            message = self.__translator.decrypt(message)
                        except DecryptError as e:
                            self.fail(message, "Decryption failure")
                            continue

                        try:
                            message = preprocess(message)
                        except GenericError as e:
                            self.fail(message, "Internal server error")
                            continue

                        try:
                            reply = handler(self, message)
                        except GenericError as e:
                            self.fail(message, "Internal server error")
                            continue

                        try:
                            reply = postprocess(reply)
                        except GenericError as e:
                            self.fail(message, "Internal server error")
                            continue

                        try:
                            reply = self.__translator.encrypt(reply)
                        except EncryptError as e:
                            self.fail(message, "Encryption failure")
                            continue
                    except:
                        self.fail(message, "Malformed message")
                        self.error(
                            "Uncaught exception: {}".format(traceback.format_exc())
                        )
                        continue

                    self.__isocket.send_string(reply)
        except KeyboardInterrupt as e:
            self.stop()

    def stop(self):
        """
        Server.stop(self)
        Stop the server
        """
        self.info("Shutting down server")
        with self.__dlock:
            self.info("Stopping polling")
            self.__done = True

        with self.__ilock:
            iaddr = self.__isocket.last_endpoint.decode()
            self.info("Unbinding interactive socket from {}".format(iaddr))
            self.__isocket.unbind(iaddr)

        with self.__block:
            baddr = self.__bsocket.last_endpoint.decode()
            self.info("Unbinding broadcast socket from {}".format(baddr))
            self.__bsocket.unbind(baddr)

        self.__listen_thread.join()

        self.info("Server stopped")


def echo(server, message):
    """
    Echo the message back to the client
    """
    server.info("Echoing {}".format(message))
    server.broadcast(message)
    return message


def stop_server(sig, frame, server):
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
