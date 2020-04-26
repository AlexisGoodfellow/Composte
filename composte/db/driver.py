#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sqlite3
from threading import Lock

# We are inspired by Django, but we're not that good at
# introspection/reflection

# ._.
def get_connection(dbname):
    """
    Open a databse connection and make sure that foreign key constraints are
    enabled for every connection, because they aren't by default and for some
    reason that can be changed _per connection_.
    """
    conn = sqlite3.connect(dbname)
    conn.execute('PRAGMA foreign_keys = "1"')  # ಠ_ಠ
    conn.commit()
    return conn


class User:
    """
    POD class representing users
    """

    def __init__(self, uname=None, hash_=None, email=None):
        self.uname = uname
        self.hash = hash_
        self.email = email

    def __str__(self):
        obj = {"type": "User", "id": self.id, "hash": self.hash, "email": self.email}
        return json.dumps(obj)


class Auth:
    """
    CRU̶D̶ wrapper for an auth table in our database
    """

    # We're so bad at CRUD that we only bother to do half of it
    __blueprint = ("username", "hash", "email")

    def __init__(self, dbname):
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
    def put(self, username, hash_, email="null"):
        """
        Create a new auth record
        """
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
    def get(self, username):
        """
        Attempt to retrieve an existing auth record
        """
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
    """
    POD class holding enough information to get to and identify composte
    projects
    """

    def __init__(self, id_=None, name=None, owner=None):
        self.id = id_
        self.name = name
        self.owner = owner

    def __str__(self):
        obj = {"type": "Project", "id": self.id, "name": self.name, "owner": self.owner}
        return """{{ "type": "Project", "id": {}, "name": {}, "owner": {} }}""".format(
            str(self.id), self.name, self.owner
        )
        # return json.dumps(obj)


# Project storage path is always
#   //<owner>/<id>.{meta,proj}
class Projects:
    """
    CRU̶D̶ wrapper for a project table in our database
    """

    __blueprint = ("id", "name", "owner")

    def __init__(self, dbname):
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

    def put(self, id_, name, owner):
        """
        Insert a project record
        """
        with self.__lock:
            self.__cursor.execute(
                """
                    INSERT INTO projects (id, name, owner)
                    VALUES (?, ?, ?)
                    """,
                (id_, name, owner),
            )
            self.__conn.commit()

    def get(self, id_):
        """
        Retrieve a project record
        """
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
    """
    CRU̶D̶ wrapper around contributor relationships between Users and Projects
    """

    def __init__(self, dbname):
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

    def put(self, username, project_id):
        """
        Add a new contributor relationship
        Or equivalently,
        Declare that username is a contributor to project_id
        """
        self.__cursor.execute(
            """
                INSERT INTO contributors (username, project_id)
                VALUES (?, ?)
                """,
            (username, project_id),
        )
        self.__conn.commit()

    def get(self, username=None, project_id=None):
        """
        Retrieve users contributing to a given project or projects
        contributable by a given user.
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

    def get_users(self, project_id):
        """
        Retrieve users who are contributors to the project
        """
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

    def get_projects(self, username):
        """
        Retrieve projects that the user can contribute to
        """
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
    except:
        pass

    auth = Auth("compose.db")
    proj = Projects("composte.db")
    own = Contributors("composte.db")

    auth.put("shark meldon", "there", "hello@composte.me")
    auth.put("save me", "whee", "saveme@composte.me")

    proj.put("1", "a", "save me")
    proj.put("2", "b", "shark meldon")

    own.put("shark meldon", "1")
    own.put("shark meldon", "2")

    # own.put("not", "real")
