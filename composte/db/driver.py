#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sqlite3
import uuid
from threading import Lock
from typing import Optional


# We are inspired by Django, but we're not that good at introspection/reflection
def get_connection(dbname: str):
    """
    Open a databse connection.

    Make sure that foreign key constraints are enabled for every connection,
    because they aren't by default and for some reason that can be changed
    _per connection_.
    """
    conn = sqlite3.connect(dbname)
    conn.execute('PRAGMA foreign_keys = "1"')  # ಠ_ಠ
    conn.commit()
    return conn


# TODO: Make me and projects dataclasses
class User:
    """POD class representing users."""

    def __init__(
        self,
        uname: Optional[str] = None,
        hash_: Optional[str] = None,
        email: Optional[str] = None,
    ):
        """Make this a dataclass."""
        self.uname = uname
        self.hash = hash_
        self.email = email

    def __str__(self):
        """Stringify."""
        obj = {"type": "User", "id": self.id, "hash": self.hash, "email": self.email}
        return json.dumps(obj)


class Auth:
    """CRU̶D̶ wrapper for an auth table in our database."""

    # We're so bad at CRUD that we only bother to do half of it
    __blueprint = ("username", "hash", "email")

    def __init__(self, dbname: str):
        """Initialize the auth database."""
        self.__conn = get_connection(dbname)
        self.__cursor = self.__conn.cursor()

        self.__cursor.execute(
            """ CREATE TABLE IF NOT EXISTS auth
                ( username TEXT PRIMARY KEY NOT NULL,
                  hash TEXT NOT NULL,
                  email TEXT)"""
        )
        self.__conn.commit()
        self.__lock = Lock()

    # Create
    def put(self, username: str, hash_: str, email: str = "null"):
        """Create a new auth record."""
        with self.__lock:
            self.__cursor.execute(
                """
                    INSERT INTO auth (username, hash, email)
                    VALUES (?, ?, ?)
                    """,
                (username, hash_, email),
            )
            self.__conn.commit()

    # Retrieve
    def get(self, username: str):
        """Attempt to retrieve an existing auth record."""
        self.__cursor.execute(
            """
                SELECT * FROM auth WHERE username=?
                """,
            (username,),
        )
        tup = self.__cursor.fetchone()
        if tup is None:
            return User(None, None, None)
        return User(*tup)


class Project:
    """Dataclass holding enough information identify composte projects."""

    def __init__(self, id_=None, name=None, owner=None):
        """Make this a dataclass."""
        self.id = id_
        self.name = name
        self.owner = owner

    def __str__(self):
        """Stringify."""
        return """{{ "type": "Project", "id": {}, "name": {}, "owner": {} }}""".format(
            str(self.id), self.name, self.owner
        )


# Project storage path is always
#   //<owner>/<id>.{meta,proj}
class Projects:
    """CRU̶D̶ wrapper for a project table in our database."""

    __blueprint = ("id", "name", "owner")

    def __init__(self, dbname: str):
        """Initialize the project database."""
        self.__conn = get_connection(dbname)
        self.__cursor = self.__conn.cursor()

        self.__cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS projects
                ( id TEXT PRIMARY KEY NOT NULL,
                  name TEXT NOT NULL,
                  owner TEXT NOT NULL REFERENCES auth(username))"""
        )

        self.__conn.commit()

        self.__lock = Lock()

    def put(self, id_: uuid.UUID, name: str, owner: str) -> None:
        """Insert a project record."""
        with self.__lock:
            self.__cursor.execute(
                """
                    INSERT INTO projects (id, name, owner)
                    VALUES (?, ?, ?)
                    """,
                (id_, name, owner),
            )
            self.__conn.commit()

    def get(self, id_: uuid.UUID):
        """Retrieve a project record."""
        self.__cursor.execute(
            """
                SELECT * FROM projects WHERE id=?
                """,
            (id_,),
        )
        tup = self.__cursor.fetchone()
        if tup is None:
            return Project(None, None, None)
        return Project(*tup)


class Contributors:
    """CRU̶D̶ wrapper around contributor relationships between Users and Projects."""

    def __init__(self, dbname: str):
        """Initialize contributor database."""
        self.__conn = get_connection(dbname)
        self.__cursor = self.__conn.cursor()

        self.__cursor.execute(
            """
                CREATE TABLE IF NOT EXISTS contributors (
                    username TEXT NOT NULL REFERENCES auth(username),
                    project_id TEXT NOT NULL REFERENCES projects(id),
                    PRIMARY KEY (username, project_id)) """
        )
        self.__conn.commit()

        self.__lock = Lock()

    def put(self, username: str, project_id: uuid.UUID) -> None:
        """
        Add a new contributor relationship.

        Equivalent to declaring that a username is a contributor to project_id
        """
        self.__cursor.execute(
            """
                INSERT INTO contributors (username, project_id)
                VALUES (?, ?)
                """,
            (username, project_id),
        )
        self.__conn.commit()

    def get(
        self, username: Optional[str] = None, project_id: Optional[uuid.UUID] = None
    ):
        """
        Retrieve users contributing to a given project.

        Alternatively, retrieve projects contributable by a given user.
        """
        # What are you even doing at this point?
        if username is None and project_id is None:
            return None
        # Want all users attached to a project
        if username is None:
            return self.get_users(project_id)
        # Want all projects attached to user
        if project_id is None:
            return self.get_projects(username)

        # ??????
        return None

    def get_users(self, project_id: Optional[uuid.UUID]):
        """Retrieve users who are contributors to the project."""
        with self.__lock:
            self.__cursor.execute(
                """
                    SELECT username FROM contributors
                    WHERE project_id=?
                    """,
                (project_id,),
            )
            users = self.__cursor.fetchall()
            return [User(*user) for user in users]

    def get_projects(self, username: Optional[str]):
        """Retrieve projects that the user can contribute to."""
        with self.__lock:
            self.__cursor.execute(
                """
                    SELECT projects.id, projects.name, projects.owner
                    FROM projects INNER JOIN contributors
                        ON projects.id = contributors.project_id
                    WHERE contributors.username = ?
                    """,
                (username,),
            )
            projects = self.__cursor.fetchall()
            return [Project(*project) for project in projects]


if __name__ == "__main__":
    import os

    try:
        os.remove("composte.db")
    except Exception:
        pass

    auth = Auth("compose.db")
    proj = Projects("composte.db")
    own = Contributors("composte.db")

    auth.put("shark meldon", "there", "hello@composte.me")
    auth.put("save me", "whee", "saveme@composte.me")

    id_1 = uuid.uuid4()
    id_2 = uuid.uuid4()

    proj.put(id_1, "a", "save me")
    proj.put(id_2, "b", "shark meldon")

    own.put("shark meldon", id_1)
    own.put("shark meldon", id_2)
