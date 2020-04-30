#!/usr/bin/env python3
"""Composte network client."""

from queue import Queue
from threading import Lock, Thread
from typing import Callable, Optional

import zmq

from composte.network.base.exceptions import DecryptError, EncryptError, GenericError
from composte.network.base.loggable import DevNull, Loggable
from composte.network.fake.security import Encryption


class Subscription(Loggable):
    """Subscription to a publishing endpoint."""

    def __init__(self, remote_address, zmq_context, logger):
        """
        Subscribe to a publishing endpoint at remote_address.

        Requires a zmq context.
        """
        super(Subscription, self).__init__(logger)

        self.__context = zmq_context

        # Subscription to remote broadcasts
        self.__addr = remote_address
        self.__socket = self.__context.socket(zmq.SUB)
        self.__socket.setsockopt_string(zmq.SUBSCRIBE, "")
        self.__socket.connect(self.__addr)

        self.__backlog = Queue(1024)
        self.__lock = Lock()

    def recv(self, poll_timeout: int = 500) -> Optional[str]:
        """
        Retrieve a message.

        Return value None after poll_timeout milliseconds.
        """
        # If we have a backlog, deal with that first, in order
        with self.__lock:
            empty = self.__backlog.empty()

            if not empty:
                msg = self.__backlog.get()
            else:
                nmsg = self.__socket.poll(poll_timeout)
                if nmsg == 0:
                    msg = None
                    return msg
                for i in range(nmsg):
                    self.__backlog.put(self.__socket.recv_string())
                msg = self.__backlog.get()

        return msg

    def stop(self) -> None:
        """Stop listening for broadcasts."""
        with self.__lock:
            self.__socket.disconnect(self.__addr)
            self.__socket.close()


# For legacy reasons, broadcast handler is separate: Subscription.
class Client(Loggable):
    """Network client for Composte."""

    __context = zmq.Context()

    def __init__(
        self, remote_address, broadcast_address, logger, encryption_scheme=Encryption()
    ):
        """
        Initialize network client for Composte.

        Opens an interactive connection and a subscription to the server.
        encryption_scheme must provide encrypt and decrypt methods
        logger must support at least the methods of base.loggable.Loggable
        """
        super(Client, self).__init__(logger)
        self.__translator = encryption_scheme

        # Interact with remote server
        self.__raddr = remote_address
        self.__isocket = self.__context.socket(zmq.REQ)
        self.__isocket.connect(self.__raddr)

        # Receive broadcasts
        self.__done = False
        self.__background = None
        self.__listener = Subscription(broadcast_address, self.__context, logger)

        self.__lock = Lock()
        self.__background_lock = Lock()

    def send(self, message: str, preprocess: Callable = lambda x: x):
        """
        Send a message down the interactive socket.

        Blocks until a reply is received.
        The reply is fed through preprocess before being returned.
        """
        with self.__lock:
            try:
                message = self.__translator.encrypt(message)
            except EncryptError as e:
                self.error(f"Failed to encrypt message {message}")
                raise e

            self.__isocket.send_string(message)
            msg = self.__isocket.recv_string()

            try:
                msg = preprocess(msg)
            except GenericError as e:
                self.error(f"Failed to preprocess message {message}")
                raise e
            return msg

    def pause_background(self):
        """Pause background actions by acquiring lock."""
        self.__background_lock.acquire()

    def resume_background(self):
        """Resume background actions by releasing lock."""
        self.__background_lock.release()

    def __message_flow(
        self, msg: str, handler: Callable, preprocess: Callable = lambda x: x
    ):
        try:
            msg = self.__translator.decrypt(msg)
        except DecryptError:
            self.error(f"Failed to decrypt {msg}")
            return

        try:
            msg = preprocess(msg)
        except GenericError:
            self.error(f"Failed to preprocess {msg}")
            return

        try:
            handler(self, msg)
        except GenericError:
            self.error(f"Failure when handling {msg}")
            return

    def __listen_almost_forever(
        self,
        handler: Callable,
        preprocess: Callable = lambda x: x,
        poll_timeout: int = 500,
    ):
        """
        Poll for messages until the client is stopped.

        Messages are pipelined through preprocess and then handler.
        """
        while True:
            with self.__lock:
                if self.__done:
                    break

            # Don't allow pausing halfway through a message
            with self.__background_lock:
                msg = self.__listener.recv(poll_timeout)
                if msg is None:
                    continue
                self.__message_flow(msg, handler, preprocess)

        self.__listener.stop()

    def start_background(
        self,
        handler: Callable,
        preprocess: Callable = lambda x: x,
        poll_timeout: int = 500,
    ):
        """
        Start thread listening for broadcasts from the remote Composte server.

        Does nothing if the thread has already been started.
        """
        with self.__lock:
            if self.__background is not None:
                return

            self.__background = Thread(
                target=self.__listen_almost_forever,
                args=(handler, preprocess, poll_timeout),
            )

            self.__background.start()

    def stop(self):
        """Stop all network activity for this Composte client."""
        self.info("Stopping client")
        with self.__lock:
            self.__isocket.disconnect(self.__raddr)
            self.__isocket.close()

            self.__done = True

        self.__background.join()
        self.__background = None

        self.info("Client stopped")


def echo(server, message: str):
    """Bash echo equivalent."""
    return message


if __name__ == "__main__":
    # Set up the servers
    s1 = Client("tcp://127.0.0.1:5000", "tcp://127.0.0.1:5001", DevNull, Encryption())
    s2 = Client("tcp://127.0.0.1:5000", "tcp://127.0.0.1:5001", DevNull, Encryption())

    # Start broadcast handlers
    s1.start_background(echo, lambda m: f"1: {m}", 500)
    s2.start_background(echo, lambda m: f"2: {m}", 500)

    # Poke the server
    for i in range(10):
        rep = s1.send("Hello there", lambda m: "1: {m}")
        print("Reply: " + rep)

        rep = s2.send("Are you there?", lambda m: f"2: {m}")
        print("Reply: " + rep)

    # Stop the clients
    s1.stop()
    s2.stop()

