#!/usr/bin/env python3

# Things that should probably be a thing:
# * Login cookies alongside project subscription cookies
# * Separation of broadcasts per project (regardless of encryption)
#       Would require moving from single broadcast to some other strategy

from composte.network.server import Server as NetworkServer
from composte.network.fake.security import Encryption
from composte.network.base.loggable import DevNull, StdErr, Combined
from composte.network.base.exceptions import GenericError
from composte.conf import logging as networkLog

from composte.protocol import client, server
from composte.auth import auth
from composte.db import driver

from composte.util import musicWrapper, bookkeeping, composteProject, timer, misc

from threading import Thread, Lock
import uuid
import json
import os
import sqlite3
import logging
import traceback


class ComposteServer:
    __project_extension = ".heap"
    __metadata_extension = ".meta"

    # I'm so sorry
    __register_lock = Lock()

    def __init__(
        self,
        interactive_port,
        broadcast_port,
        logger,
        encryption_scheme,
        data_root="data/",
    ):
        """
        Start a Composte Server listening on interactive_port and broadcasting
        on broadcast_port. Logs are directed to logger, messages are
        transparently encrypted with encryption_scheme.encrypt() and
        encryption_scheme.decrypt(), and data is stored in the directory
        data_root.
        """

        self.__server = NetworkServer(
            interactive_port, broadcast_port, logger, encryption_scheme
        )

        self.__server.start_background(
            self.__handle, self.__preprocess, self.__postprocess
        )

        self.__users = None
        self.__projects = None
        self.__contributors = None

        self.version = misc.get_version()
        self.__server.info("Composte server version {}".format(self.version))

        self.__data_root = data_root
        self.__project_root = os.path.join(self.__data_root, "users")

        self.__dlock = Lock()
        self.__done = False

        self.__pool = bookkeeping.ProjectPool()
        # A better solution would have a lock for every project, but in a
        # classroom demo this won't be an issue
        self.__flushing = Lock()

        def is_done(self):
            with self.__dlock:
                return not self.__done

        self.__timer = timer.every(
            300, 2, lambda: self.__pool.map(self.flush_project), lambda: is_done(self)
        )

        try:
            os.makedirs(self.__project_root)
        except FileExistsError as e:
            pass

        self.sessions = {}

    def flush_project(self, project, count):
        """
        Flush project to backing storage
        """
        with self.__flushing:
            self.write_project(project)

    # Database interactions

    def register(self, uname, pword, email):
        """
        Register a new user. Username must be unique per user database.
        """
        hash_ = auth.hash(pword)

        with ComposteServer.__register_lock:
            hopefully_None = self.__users.get(uname)
            if hopefully_None.uname is not None:
                return ("fail", "Username is taken")

            # Apparently exceptions on writes cause the database to lock...
            try:
                self.__users.put(uname, hash_, email)
            except sqlite3.IntegrityError:
                return ("fail", "Username is taken")
            except sqlite3.DatabaseError as e:
                # raise e
                return ("fail", "Generic failure")

        try:
            os.mkdir(os.path.join(self.__project_root, uname))
        except FileExistsError as e:
            pass

        return ("ok", "")

    def login(self, uname, pword):
        """
        Log a user in
        """
        record = self.__users.get(uname)
        if record.hash is None:
            return ("fail", "failed to login")

        success = auth.verify(pword, record.hash)
        if success:
            uuids = self.__contributors.get_projects(uname)
            project_ids = [str(uuid_) for uuid_ in uuids]
            return ("ok", json.dumps(project_ids))
        else:
            return ("fail", "failed to login")

    def create_project(self, uname, pname, metadata):
        """
        Create a new Composte project. Projects are given unique identifiers,
        so project names need not be unique.
        """
        metadata = json.loads(metadata)
        metadata["name"] = pname
        metadata["owner"] = uname

        proj = composteProject.ComposteProject(metadata)
        id_ = str(proj.projectID)

        hopefully_not_None = self.__users.get(uname)
        if hopefully_not_None is None:
            return ("fail", "User {} is not registered".format(uname))

        self.write_project(proj)

        self.__server.info(
            "Creating project {} with name {} for {}".format(
                id_, metadata["name"], uname
            )
        )

        try:
            self.__projects.put(id_, pname, uname)
        except sqlite3.OperationalError as e:
            self.__server.info("?????????????")
            raise GenericError("The database is borked")

        p = self.__projects.get(id_)
        print(p)

        # This could then potentially also lock the database...
        try:
            self.__contributors.put(uname, id_)
        except sqlite3.IntegrityError as e:
            raise e
            return ("fail", "User {} is not registered".format(uname))

        return ("ok", id_)

    def get_project_over_the_wire(self, pid):
        """
        Retrieve the serialized form of a project for transmission. Currently
        only used during the initial handshake.
        """
        proj = self.__pool.put(pid, lambda: self.get_project(pid)[1])
        self.__pool.remove(pid)

        if type(proj) == str:
            return ("fail", "What even is that")

        return ("ok", json.dumps(proj.serialize()))

    def get_project(self, pid):
        """
        Fetch a Composte project object for manipulation.
        Not suitable for use as a top-level handler
        """
        project_entry = self.__projects.get(pid)
        if project_entry.id == None:
            return ("fail", "Project not found")

        pid = project_entry.id
        owner = project_entry.owner

        proj = self.read_project(pid)

        return ("ok", proj)

    def list_projects_by_user(self, uname):
        """
        Retrieve a list of projects that a user is a collaborator on
        """
        listings = self.__contributors.get(username=uname)
        listings = [str(project) for project in listings]
        return ("ok", json.dumps(listings))

    def list_contributors_of_project(self, pid):
        """
        Retrieve a list of a project's contributors
        """
        listings = self.__contributors.get(project_id=pid)
        listings = [str(user) for user in listings]
        return ("ok", json.dumps(listings))

    def compare_versions(self, client_version):
        """
        Compare version hashes
        """
        if client_version != self.version:
            status = "fail"
            response = (status, self.version)
        else:
            status = "ok"
            reason = ""
            response = (status, reason)

        return response

    # Utility

    def write_project(self, project):
        """
        I'm going to cheat for now and dump to the filesystem. Ideally we
        write to a database, but that requires more work. Either way, that can
        be hidden in this function
        """
        user = project.metadata["owner"]
        id_ = str(project.projectID)

        (metadata, parts, _) = project.serialize()

        base_path = os.path.join(self.__project_root, user)
        base_path = os.path.join(base_path, id_)
        with open(base_path + self.__metadata_extension, "w") as f:
            f.write(metadata)

        with open(base_path + self.__project_extension, "w") as f:
            f.write(parts)

    def read_project(self, pid):
        """
        We've cheated and the projects live on the filesystem. Ideally we want
        them in a database, but that's work. Either way, we hide the true
        locations of projects inside of this function.
        """

        owner = self.__projects.get(pid).owner

        filename = pid + self.__metadata_extension
        relpath = os.path.join(owner, filename)
        fullpath = os.path.join(self.__project_root, relpath)
        with open(fullpath, "r") as f:
            metadata = f.read()

        filename = pid + self.__project_extension
        relpath = os.path.join(owner, filename)
        fullpath = os.path.join(self.__project_root, relpath)
        with open(fullpath, "r") as f:
            parts = f.read()

        project = composteProject.deserializeProject((metadata, parts, pid))
        # Don't put it into the pool yet, because then we end up with a
        # use count that will never be 0 again
        return project

    # Cookie: uuid
    def generate_cookie_for(self, user, project):
        """
        We don't bother checking for UUID collisions, since they "don't"
        happen
        """
        cookie = uuid.uuid4()
        self.sessions[cookie] = (user, project)
        return cookie

    # Session: {user, project_id}
    # May need login cookies too
    def cookie_to_session(self, cookie):
        """
        Retrieve the session associated with a cookie
        """
        try:
            cookie = uuid.UUID(cookie)
        except ValueError as e:
            return ("fail", "That doesn't look like a cookie")

        try:
            session = self.sessions[cookie]
        except KeyError as e:
            return None
        return session

    def remove_cookie(self, cookie):
        """
        Remove a cookie and its associated session
        """
        try:
            cookie = uuid.UUID(cookie)
        except ValueError as e:
            return ("fail", "That doesn't look like a cookie")

        try:
            del self.sessions[cookie]
        except KeyError as e:
            return ("fail", "Who are you")

        return ("ok", "")

    def do_update(self, *args):
        """
        Perform a music-related update, deferring to
        musicWrapper.performMusicFperformMusicFun
        """

        # Use this function to get a project
        pid_ = None

        def get_fun(pid):
            """
            Fetch a project from the cache
            """
            # The client musicfuns shouldn't have to worry about how the
            # server manages the lifetimes of project objects
            proj = self.__pool.put(pid, lambda: self.get_project(pid)[1])
            # We need to steal the pid to release it later
            pid_ = pid
            return proj

        with self.__flushing:
            try:
                # We still need to provide a way to get the project
                reply = musicWrapper.performMusicFun(*args, fetchProject=get_fun)
            except:
                print(traceback.format_exc())
                return ("fail", "Internal Server Error")
            return reply

            # We can't decrement the refcount before now, because we could
            # cause an early flush otherwise, and then serverside persistence
            # is breaks.
            self.__pool.remove(pid_, self.write_project)

    def subscribe(self, username, pid):
        """
        Subscribe a client to updates for a project. Pins the project in the
        cache
        """
        # Assert permission
        contributors = self.__contributors.get(project_id=pid)
        contributors = [user.uname for user in contributors]
        if username in contributors:
            self.__pool.put(pid, lambda: self.get_project(pid)[1])
            cookie = self.generate_cookie_for(username, pid)
            return ("ok", str(cookie))
        else:
            self.__server.debug("{} is not one of {}".format(username, contributors))
            return ("fail", "You are not a contributor")

    def unsubscribe(self, cookie):
        """
        Unsubscribe a client from a project. Unpins the project in the cache
        """
        session = self.cookie_to_session(cookie)

        if session is None:
            return ("fail", "You are not subscribed")

        (user, project_id) = session
        (status, reason) = self.remove_cookie(cookie)

        if status == "ok":
            project = self.__pool.put(project_id, lambda x: self.get_project(x)[1])
            pid = project.projectID
            self.__pool.remove(pid, lambda x: self.write_project(x))

        return (status, reason)

    # Packaged for neatness
    def get_db_connections(self):
        """
        Open database connections if they are not already open
        """
        dbname = "data/composte.db"

        if self.__users is None:
            self.__users = driver.Auth(dbname)

        if self.__projects is None:
            self.__projects = driver.Projects(dbname)

        if self.__contributors is None:
            self.__contributors = driver.Contributors(dbname)

    def share(self, pid, new_contributor):
        """
        Add a new user to the list of contributors to a project
        """

        contributors = self.__contributors.get(project_id=pid)
        user = self.__users.get(new_contributor)

        # If that's not a known user, fail
        if user.uname is None:
            return ("fail", "Who is that")

        # If they are already a contributor, nothing to do
        if new_contributor not in contributors:
            # If that's not a valid project, fail
            try:
                self.__contributors.put(new_contributor, pid)
            except sqlite3.IntegrityError as e:
                return ("fail", "What project is that")

        return ("ok", "")

    # Handlers

    def __handle(self, _, rpc):
        """
        Dispatch to handle messages
        """
        self.get_db_connections()

        def fail(*args):
            return ("fail", "I don't know what you want me to do")

        def unimplemented(*args):
            return ("?", "?")

        rpc_funs = {
            "register": self.register,
            "login": self.login,
            "create_project": self.create_project,
            "list_projects": self.list_projects_by_user,
            "get_project": self.get_project_over_the_wire,
            "subscribe": self.subscribe,
            "unsubscribe": self.unsubscribe,
            "update": self.do_update,
            "handshake": self.compare_versions,
            "share": self.share,
        }

        self.__server.debug(rpc)
        f = rpc["fName"]

        do_rpc = rpc_funs.get(f, fail)

        try:
            # This is expected to be a tuple of things to send back
            (status, other) = do_rpc(*rpc["args"])
        except GenericError as e:
            return ("fail", "Internal server error")
        except:
            self.__server.error(traceback.format_exc())
            return ("fail", "Internal server error (Developer error)")

        # Only broadcast successful updates
        if f == "update" and status == "ok":
            self.__server.broadcast(client.serialize(rpc["fName"], *rpc["args"]))

        return (status, other)

    def __preprocess(self, message):
        """
        Deserialize messages for consumption by __handle
        """
        return client.deserialize(message)

    def __postprocess(self, reply):
        """
        Serialize replies to be sent over the wire
        """
        reply_str = server.serialize(*reply)
        self.__server.debug(reply_str)
        return reply_str

    def stop(self):
        """
        Stop the server elegantly
        """
        self.__server.info("ComposteServer shutting down")
        with self.__dlock:
            self.__done = True

        self.__timer.join()
        self.__pool.map(self.flush_project)

        self.__server.stop()


def stop_server(sig, frame, server):
    """
    Signal handler to stop the server elegantly, especially under a supervisor
    """
    server.stop()


if __name__ == "__main__":
    import signal

    import argparse

    parser = argparse.ArgumentParser(
        prog="ComposteServer", description="A Composte Server"
    )

    parser.add_argument("-i", "--interactive-port", default=5000, type=int)
    parser.add_argument("-b", "--broadcast-port", default=5001, type=int)

    args = parser.parse_args()

    print("Composte server version {}".format(misc.get_version()))

    networkLog.setup()
    log = logging.getLogger("main")

    real_log = Combined((log, StdErr))

    s = ComposteServer(
        "tcp://*:{}".format(args.interactive_port),
        "tcp://*:{}".format(args.broadcast_port),
        real_log,
        Encryption(),
    )

    signal.signal(signal.SIGINT, lambda sig, f: stop_server(sig, f, s))
    signal.signal(signal.SIGQUIT, lambda sig, f: stop_server(sig, f, s))
    signal.signal(signal.SIGTERM, lambda sig, f: stop_server(sig, f, s))
    signal.signal(signal.SIGHUP, lambda sig, f: stop_server(sig, f, s))
