# Composte
## Get together to make bad music

*To our beloved professor:* Before you print out every single line of python
source code in this repository, please run the following command before
committing to your decision.

    find . -name '*.py' | xargs wc -l

We apologize in advance. We also wish to offer our condolences to you, the
course staff, and the trees who gave their lives so that this code may be
briefly read.

<hr/>

For even worse documentation, see [docs](doc/index.md).

## Getting Composte

In general, you can fetch the latest stable version from here:

    git clone https://github.com/AlexisGoodfellow/Composte.git

Occasionally, you may find that the server you are connecting to uses a
different version, and you will have to obtain a client of that version. One
of these days we'll figure out how you can do that.

## Building and Running

Composte is aimed at \*NIX systems. If you are running Windows and manage to
get a server or client running, please tell us how you did it!

The Composte client and server provided here are `python3` applications and do
not require compilation. However, the use of a virtual environment such as
`virtualenv` or `venv` is recommended.

General setup:

There are a number of non-python dependencies for clients that we recommend
you satisfy before satisfying the python dependencies. If you only plan on
running the Composte server, these packages are not required.

    timidity
    timidity-interfaces-extra
    freepats

Composte has a number of python dependencies, listed in `requirements.txt`.

    pip install -r requirements.txt

If you will be relying on systemwide packages, refer to `requirements.txt` for
a list of python packages that are required.

In general, you shouldn't be starting Composte servers manually outside of
testing or demos. It is recommended that you run it as a service using a
supervisor of your choice.

By default, Composte servers listen on port 5000 and send outgoing traffic on
ports 5000 and 5001. If you are running from behind a firewall, make sure that
these ports or the ones you choose to use are not filtered.

To start a Composte server:

    ./ComposteServer.py

The server accepts arguments to control which ports it uses. The broadcast
port only sees outgoing traffic, while the interactive port sees both incoming
and outgoing traffic.

To start a Composte client:

    ./ComposteClient.py [-r Remote-address]

The most commonly used option to `ComposteClient` is `-r Remote-address`,
the remote address where the server you want to connect to is listening.

__Docker__

We also provide a Dockerfile describing a container that runs a Composte
Server. The container listens on port 5000 and 5001.

The following is a reiteration of what was required to successfully run the
container with output persistence in our development environment. We may be
wrong in the general case.

If you wish to retain logs, you must mount a directory to
`/=\ /usr/src/app/logs`. If you wish to retain projects, user, etc, you must
mount a directory to `/=\ /usr/src/app/data`.

A one-time, standalone invocation of the container might look like this:

    docker build -t composte-server .
    docker run -p 0.0.0.0:5000:5001 -p 0.0.0.0:5001:5001 \
    -v $(pwd)/logs:/=\ /usr/src/logs -v $(pwd)/data:/=\ /usr/src/data \
    composte-server

Clients are run as usual in this case.

## Source Code Tourist's Guide

For your viewing pleasure or displeasure, we provide an elided `tree` of the
repository.

[Skip](#source-descriptions)

    Composte
    ├── auth
    │   └── auth.py
    ├── client
    │   └── < GUI Suffering >
    ├── ComposteClient.py
    ├── ComposteServer.py
    ├── data
    │   ├── composte.db
    │   └── users
    │       └── < User data >
    ├── database
    │   └── driver.py
    ├── demoScripts
    │   └── < Demonstration scripts >
    ├── doc
    │   ├── architecture
    │   │   └── index.md
    │   ├── deliverables
    │   │   └── index.md
    │   ├── images
    │   │   └── Bad_Diagrams
    │   │       └── < "Diagrams" >
    │   ├── index.md
    │   └── protocol
    │       └── index.md
    ├── Dockerfile
    ├── html
    │   ├── index.html
    │   └── styles
    │       └── composte.css
    ├── logs
    │   └── < Logs >
    ├── network
    │   ├── base
    │   │   ├── exceptions.py
    │   │   ├── handler.py
    │   │   └── loggable.py
    │   ├── client.py
    │   ├── conf
    │   │   ├── logging.conf
    │   │   └── logging.py
    │   ├── dns.py
    │   ├── fake
    │   │   └── security.py
    │   └── server.py
    ├── protocol
    │   ├── base
    │   │   └── exceptions.py
    │   ├── client.py
    │   └── server.py
    ├── README.md
    ├── requirements.txt
    └── util
        ├── bookkeeping.py
        ├── classExceptions.py
        ├── composteProject.py
        ├── misc.py
        ├── musicFuns.py
        ├── musicWrapper.py
        ├── repl.py
        └── timer.py

## Source Descriptions

__Top Level__

`ComposteServer.py` implements a complete Composte server on top of the
network server.

`ComposteClient.py` implements most of a Composte client on top of the network
client.

__auth__

`auth.py` contains functions to create and verify password hashes.

__database__

`driver.py` encapsulates access to the the database. It translates between
database schemas and python objects.

__network__

`client.py` provides a network client.

`server.py` provides a network server.

`dns.py` provides methods to get ip addresses from domain names.

__network/base__

`exceptions.py` contains exceptions the network clients and servers expect
users to raise in the event of trouble.

`handler.py` provides a base class for a stateful message handler. Users may
choose to derive their message handlers from this.

`loggable.py` provides a base class to provide simpler logging.

__network/fake__

`security.py` provides classes conforming to the `encryption_scheme` interface
that the network servers and clients expect, but provide no encryption.

__network/conf__

`logging.py` contains the default logging configuration that the network
clients and servers use, as well as a method to read that configuration.

__client__

This module contains the GUI.

__doc__

This directory contains documentation of the project and deliverables for
COMP 50CP. Much of the documentation is out of date, and a fair amount may
also be unreachable from internal links.

__protocol__

`client.py` contains methods for serializing and deserializing client
messages.

`server.py` contains methods for serializing and deserializing server
messages.

__protocol/base__

`exceptions.py` contains exceptions that the `protocol` module may raise.

__util__

The `util` module implements a number of miscellaneous things that are needed
to make the server work. Notably, the music backend is implemented here

`bookkeeping.py` implements two static object pools.

`classExceptions.py` provides some exceptions used in the class hierarchy used
by the GUI.

`composteProject.py` provides the internal, in-memory representation of a
project. This also provides serialization and deserialization facilities.

`misc.py` provides a function to get the version (commit) hash.

`musicFuns.py` provides the mutators for the internal representation of music.

`musicWrapper.py` provides a thin wrapper around `musicFuns.py`, conforming to
the message handler contracts that `ComposteServer` expects.

`timer.py` provides a method to run a function at a configurably approximate
interval.

`repl.py` provides the REPL shell/scripting interface that Composte has
decomposed into. The REPL is likely to have access to all methods that the GUI
exposes to the user, and indeed may have finer-grained access to music
manipulation methods. The REPL is feature-impoverished, but capable of just
enough to be semi-useful.

