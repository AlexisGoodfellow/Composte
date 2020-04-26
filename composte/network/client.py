#!/usr/bin/env python3

from queue import Queue
from threading import Lock, Thread

import zmq

from network.base.exceptions import DecryptError, EncryptError, GenericError
from network.base.loggable import DevNull, Loggable
from network.fake.security import Encryption, Log


class Subscription(Loggable):
    def __init__(self, remote_address, zmq_context, logger):
        """
        Subscription.__init__(self, remote_address, zmq_context)
        Subscription to a publishing endpoint at remote_address
        Requires a zmq context
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

    def recv(self, poll_timeout=500):
        """
        Subscription.recv(self, poll_timeout = 500)
        Retrieve a message, failing with return value None after poll_timeout
        milliseconds.
        Returns string on success, None on failure
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

    def stop(self):
        """
        Subscription.stop(self)
        Stop listening for broadcasts
        """
        with self.__lock:
            self.__socket.disconnect(self.__addr)
            self.__socket.close()


# For legacy reasons, broadcast handler is separate: Subscription.
class Client(Loggable):
    __context = zmq.Context()

    def __init__(
        self, remote_address, broadcast_address, logger, encryption_scheme=Encryption()
    ):
        """
        Client.__init__(self, remote_address, broadcast_address,
            logger, encryption_scheme = Encryption())
        Network client for Composte. Opens an interactive connection and a
        subscription to the server.
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

    def send(self, message, preprocess=lambda x: x):
        """
        Client.send(self, message, preprocess = lambda msg: msg)
        Send a message down the interactive socket, blocking until a reply is
        received.
        The reply is fed through preprocess before being returned
        """
        with self.__lock:
            try:
                message = self.__translator.encrypt(message)
            except EncryptError as e:
                self.error("Failed to encrypt message {}".format(message))
                raise e

            self.__isocket.send_string(message)
            msg = self.__isocket.recv_string()

            try:
                msg = preprocess(msg)
            except GenericError as e:
                self.error("Failed to preprocess message {}".format(message))
                raise e
            return msg

    def pause_background(self):
        self.__background_lock.acquire()

    def resume_background(self):
        self.__background_lock.release()

    def __listen_almost_forever(
        self, handler, preprocess=lambda x: x, poll_timeout=500
    ):
        """
        Client.__listen_almost_forever(self, handler,
            preprocess = lambda msg: msg, poll_timeout = 500)
        Poll for messages until the client is stopped
        Messages are pipelined through preprocess and then handler.
        """
        while True:
            with self.__lock:
                if self.__done:
                    break

            # Don't allow pausing halfway through a message
            with self.__background_lock:
                msg = self.__listener.recv(poll_timeout)
                if msg == None:
                    continue

                try:
                    msg = self.__translator.decrypt(msg)
                except DecryptError as e:
                    self.error("Failed to decrypt {}".format(msg))
                    continue

                try:
                    msg = preprocess(msg)
                except GenericError as e:
                    self.error("Failed to preprocess {}".format(msg))
                    continue

                try:
                    handler(self, msg)
                except GenericError as e:
                    self.error("Failure when handling {}".format(msg))
                    continue

        self.__listener.stop()

    def start_background(self, handler, preprocess=lambda x: x, poll_timeout=500):
        """
        Client.start_background(self, handler, preprocess = lambda msg: msg,
            poll_timeout = 500)
        Hands off to Client.__listen_almost_forever
        Start thread listening for broadcasts from the remote Composte server
        Does nothing if the thread has already been started
        """
        with self.__lock:
            if self.__background != None:
                return

            self.__background = Thread(
                target=self.__listen_almost_forever,
                args=(handler, preprocess, poll_timeout),
            )

            self.__background.start()

    def stop(self):
        """
        Client.stop(self)
        Stop all network activity for this Composte client
        """
        self.info("Stopping client")
        with self.__lock:
            self.__isocket.disconnect(self.__raddr)
            self.__isocket.close()

            self.__done = True

        self.__background.join()
        self.__background = None

        self.info("Client stopped")


def echo(server, message):
    return message


def id(pre, elem):
    return pre + elem


if __name__ == "__main__":
    # Set up the servers
    s1 = Client("tcp://127.0.0.1:5000", "tcp://127.0.0.1:5001", DevNull, Encryption())
    s2 = Client("tcp://127.0.0.1:5000", "tcp://127.0.0.1:5001", DevNull, Encryption())

    # Start broadcast handlers
    s1.start_background(echo, lambda m: id("1: ", m), 500)
    s2.start_background(echo, lambda m: id("2: ", m), 500)

    # Poke the server
    for i in range(10):
        rep = s1.send("Hello there", lambda m: id("1: ", m))
        print("Reply: " + rep)

        rep = s2.send("Are you there?", lambda m: id("2: ", m))
        print("Reply: " + rep)

    # Stop the clients
    s1.stop()
    s2.stop()
