#!/usr/bin/env python3

from network.client import Client as NetworkClient
from network.fake.security import Encryption
from network.base.loggable import DevNull, StdErr
from network.base.exceptions import GenericError

from client import editor

from protocol import client, server
from util import misc
from threading import Thread, Lock
from util.repl import the_worst_repl_you_will_ever_see
import util.musicFuns
import util.musicWrapper
import util.composteProject
import json
import music21
import traceback
import uuid
import subprocess
import shlex
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.Qt import Q_ARG, Q_RETURN_ARG

DEBUG = False


class ComposteClient(QtCore.QObject):

    _updateGUI = QtCore.pyqtSignal(float, float, name="_updateGUI")
    _chatToGUI = QtCore.pyqtSignal(str, name="_chatToGUI")

    def __init__(
        self,
        interactive_remote,
        broadcast_remote,
        logger,
        encryption_scheme,
        *args,
        **kwargs,
    ):
        """
        RPC host for connecting to Composte Servers. Connects to a server
        listening at interactive_remote and broadcasting on on
        broadcast_remote. Logs are directed to logger, and messages are
        transparently encrypted and encrypted with
        encryption_scheme.encrypt() and decrypted with
        encryption_scheme.decrypt().
        Broadcasts are handled with broadcast_handler
        """
        super(ComposteClient, self).__init__(*args, **kwargs)

        self.__client = NetworkClient(
            interactive_remote, broadcast_remote, logger, encryption_scheme
        )

        self.__client.info(
            "Connecting to {} and {}".format(interactive_remote, broadcast_remote)
        )

        self.__version_handshake()

        self.__project = None
        self.__editor = None

        self.__tts = False

        espeak = subprocess.check_output(
            "which espeak | cat -", stderr=subprocess.DEVNULL, shell=True
        )
        say = subprocess.check_output(
            "which say | cat -", stderr=subprocess.DEVNULL, shell=True
        )
        if espeak.decode() != "":
            self.__ttsCommand = "espeak "
        elif say.decode() != "":
            self.__ttsCommand = "say "
        else:
            self.__ttsCommand = None

        # If this happens too early, a failed version handshake prevents this
        # thread from ever being joined, and the application will never exit
        self.__client.start_background(self.__handle)

    def project(self):
        return self.__project

    def pause_updates(self):
        """
        Prevent incoming updates from being applied, queuing them up.  Blocks
        until all updates currently being processed have completed.
        """
        self.__client.pause_background()

    def resume_update(self):
        """
        Apply queued updates and resume applying updates as they come in.
        """
        self.__client.resume_background()

    def closeEditor(self):
        """
        To be run when the editor exits, to do cleanup that will allow it to be
        relaunched later.
        """
        self.__editor = None

    def __updateGui(self, startOffset, endOffset):
        """
        Tell the GUI to update the section of the score between startOffset and
        endOffset.
        """
        if self.__editor is not None:
            self._updateGUI.emit(startOffset, endOffset)

    def __handle(self, _, rpc):
        def fail(*args):
            return ("fail", "I don't know what you want me to do")

        def unimplemented(*args):
            return ("?", "?")

        rpc_funs = {"update": self.__do_update}

        rpc = client.deserialize(rpc)
        if self.__project is None or str(self.__project.projectID) != rpc["args"][0]:
            return
        f = rpc["fName"]
        if rpc["args"][1] == "chat":
            rpc["args"][2] = json.loads(rpc["args"][2])

            printedStr = rpc["args"][2][0] + ": " + rpc["args"][2][1]
            spokenStr = shlex.quote(rpc["args"][2][0] + " says " + rpc["args"][2][1])
            print(printedStr)
            self._chatToGUI.emit(printedStr)
            if self.__tts and (self.__ttsCommand is not None):
                subprocess.call(
                    str(self.__ttsCommand) + spokenStr,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    shell=True,
                )
            return

        do_rpc = rpc_funs.get(f, fail)
        try:
            (status, other) = do_rpc(*rpc["args"])
            if status == "ok":
                startOffset, endOffset = other
                self.__updateGui(startOffset, endOffset)
        except Exception as e:
            print(e)

    def __do_update(self, *args):
        project = lambda x: self.__project

        try:
            return util.musicWrapper.performMusicFun(*args, fetchProject=project)

        except:
            print(traceback.format_exc())
            return ("fail", "error")

    def __version_handshake(self):
        """
        Perform a version handshake with the remote Composte server
        """
        msg = client.serialize("handshake", misc.get_version())
        reply = self.__client.send(msg)
        if DEBUG:
            print(reply)
        reply = server.deserialize(reply)
        if reply[0] == "fail":
            status, reason = reply
            version = reason[0]
            raise GenericError(version)

    def register(self, uname, pword, email):
        """
        register username password email

        Attempt to register a new user
        """
        msg = client.serialize("register", uname, pword, email)
        reply = self.__client.send(msg)
        if DEBUG:
            print(reply)
        return server.deserialize(reply)

    # We probably need cookies for login too, otherwise people can request
    # project listings (and thus projects) and subscribe to projects they
    # shouldn't be able to. This isn't an issue for the minimum deliverable
    # for the course, but it is an issue in the long run
    def login(self, uname, pword):
        """
        login username password

        Attempt to login as a user
        """
        msg = client.serialize("login", uname, pword)
        reply = self.__client.send(msg)
        # status, reason = reply
        if DEBUG:
            print(reply)
        return server.deserialize(reply)

    def create_project(self, uname, pname, metadata):
        """
        create-project username project-name metadata

        Attempt to create a project. Metdata must have the form of a json
        object, eg "{ "owner": username }"
        """
        if type(metadata) == str:
            metadata = json.loads(metadata)
        metadata["owner"] = uname
        metadata["name"] = pname
        metadata = json.dumps(metadata)
        msg = client.serialize("create_project", uname, pname, metadata)
        reply = self.__client.send(msg)
        if DEBUG:
            print(reply)
        try:
            return server.deserialize(reply)
        except:
            print(reply)
            return ("fail", "Mangled reply")

    def share(self, pid, new_contributor):
        """
        share project-id new-contributor

        Allow another person to contribute to your project
        """
        msg = client.serialize("share", pid, new_contributor)
        reply = self.__client.send(msg)
        if DEBUG:
            print(reply)
        return server.deserialize(reply)

    def retrieve_project_listings_for(self, uname):
        """
        list-projects username

        Get a list of all projects this user is a collaborator on
        """
        msg = client.serialize("list_projects", uname)
        reply = self.__client.send(msg)
        return server.deserialize(reply)

    def get_project(self, pid):
        """
        get-project project-id

        Given a uuid, get the project to work on
        """
        msg = client.serialize("get_project", pid)
        reply = server.deserialize(self.__client.send(msg))
        if DEBUG:
            print(reply)
        status, ret = reply
        if status == "ok":
            print(type(ret))
            realProj = json.loads(ret[0])
            self.__project = util.composteProject.deserializeProject(realProj)
        return reply

    # Realistically, we send a login cookie and the server determines the user
    # from that, but we don't have that yet
    def subscribe(self, uname, pid):
        """
        subscribe username project-id

        Subscribe to updates to a project
        """
        msg = client.serialize("subscribe", uname, pid)
        reply = self.__client.send(msg)
        # print(reply)
        j = json.loads(reply)
        if DEBUG:
            print(j[1][0])
        return server.deserialize(reply)

    def unsubscribe(self, cookie):
        """
        Unsubscribe to updates to a project
        """
        msg = client.serialize("unsubscribe", cookie)
        reply = self.__client.send(msg)
        if DEBUG:
            print(reply)
        return server.deserialize(reply)

    # There's nothing here yet b/c we don't know what anything look like
    def update(self, pid, fname, args, partIndex=None, offset=None):
        """
        update project-id update-type args partIndex = None offset = None

        Send a music related update for the remote backend to process. args is
        a tuple of arguments
        """
        args = json.dumps(args)
        msg = client.serialize("update", pid, fname, args, partIndex, offset)
        reply = self.__client.send(msg)
        if DEBUG:
            print(reply)
        return server.deserialize(reply)

    def chat(self, pid, from_, *message_parts):
        """
        chat project-id sender [message-parts]
        """
        return self.update(pid, "chat", (from_, " ".join(message_parts)))

    def toggleTTS(self):
        """
        toggle-tts

        If text-to-speech is turned on, toggle-tts turns it off.
        If text-to-speech is turned off, toggle-tts turns it on.
        Text-to-speech will only work if it is availible.
        """
        self.__tts = not self.__tts

    def ttsOn(self):
        """
        tts-on

        Turns text-to-speech on if it is availible.
        """
        self.__tts = True

    def ttsOff(self):
        """
        tts-off

        Turns text-to-speech off.
        """
        self.__tts = False

    def changeKeySignature(self, pid, offset, partIndex, newSigSharps):
        """
        change-key-signature project-id offset partIndex newSigSharps

        Change the key signature
        """
        return self.update(
            pid,
            "changeKeySignature",
            (offset, partIndex, newSigSharps),
            partIndex,
            offset,
        )

    def insertNote(self, pid, offset, partIndex, pitch, duration):
        """
        insert-note project-id offset partIndex pitch duration

        Insert a note into the score
        """
        return self.update(
            pid, "insertNote", (offset, partIndex, pitch, duration), partIndex, offset
        )

    def removeNote(self, pid, offset, partIndex, removedNoteName):
        """
        remove-note project-id offset partIndex removedNoteName

        Remove a note from the score
        """
        return self.update(
            pid, "removeNote", (offset, partIndex, removedNoteName), partIndex, offset
        )

    def insertMetronomeMark(self, pid, offset, bpm):
        """
        insert-metronome-mark project-id offset bpm pulseDuration

        Insert a metronome mark
        """
        return self.update(pid, "insertMetronomeMark", (offset, bpm), None, offset)

    def removeMetronomeMark(self, pid, offset):
        """
        remove-metronome-mark project-id offset

        Remove a metronome mark
        """
        return self.update(pid, "removeMetronomeMark", (offset,), None, offset)

    def transpose(self, pid, partIndex, semitones):
        """
        transpose project-id partIndex semitones


        """
        return self.update(pid, "transpose", (partIndex, semitones), partIndex, None)

    def insertClef(self, pid, offset, partIndex, clefStr):
        """
        insert-clef project-id offset partIndex clefStr

        Insert a clef
        """
        return self.update(
            pid, "insertClef", (offset, partIndex, clefStr), partIndex, offset
        )

    def removeClef(self, pid, offset, partIndex):
        """
        remove-clef project-id offset partIndex

        Remove a clef
        """
        return self.update(pid, "removeClef", (offset, partIndex), partIndex, offset)

    def insertMeasures(self, pid, insertionOffset, partIndex, insertedQLs):
        """
        insert-measures project-id insertionOffset partIndex insertedQLs

        Insert measures into the score
        """
        return self.update(
            pid,
            "insertMeasures",
            (insertionOffset, partIndex, insertedQLs),
            partIndex,
            insertionOffset,
        )

    def addInstrument(self, pid, offset, partIndex, instrumentStr):
        """
        add-instrumnet project-id offset partIndex instrumentStr
        """
        return self.update(
            pid, "addInstrument", (offset, partIndex, instrumentStr), partIndex, offset
        )

    def removeInstrument(self, pid, offset, partIndex):
        """
        remove-instrument project-id offset partIndex
        """
        return self.update(
            pid, "removeInstrument", (offset, partIndex), partIndex, offset
        )

    def addDynamic(self, pid, offset, partIndex, dynamicStr):
        """
        add-dynamic project-id offset partIndex dynamicStr
        """
        return self.update(
            pid, "addDynamic", (offset, partIndex, dynamicStr), partIndex, offset
        )

    def removeDynamic(self, pid, offset, partIndex):
        """
        remove-dynamic project-id offset partIndex
        """
        return self.update(pid, "removeDynamic", (offset, partIndex), partIndex, offset)

    def addLyric(self, pid, offset, partIndex, lyric):
        """
        add-lyric project-id offset partIndex lyric

        Attach a lyric to the score
        """
        return self.update(
            pid, "addLyric", (offset, partIndex, lyric), partIndex, offset
        )

    def startEditor(self):
        """
        start-editor

        Launch the editor GUI.
        """
        if self.__project is not None:
            if self.__editor is None:
                self.__editor = editor.Editor(self)
                self.__editor.showMaximized()

        else:
            return "Load a project before launching the editor."

    def playback(self, partIndex):
        """
        playback partIndex

        Playback the project set by get-project.
        """
        self.pause_updates()
        util.musicFuns.playback(self.__project.parts[int(partIndex)])
        self.resume_update()

    def stop(self):
        """
        Stop the client elegantly
        """
        self.__client.stop()


if __name__ == "__main__":
    import sys

    from network import dns

    import argparse

    parser = argparse.ArgumentParser(
        prog="ComposteClient", description="A Composte Client"
    )

    parser.add_argument("-i", "--interactive-port", default=5000, type=int)
    parser.add_argument("-b", "--broadcast-port", default=5001, type=int)
    parser.add_argument("-r", "--remote-address", default="composte.me", type=str)
    parser.add_argument("-f", "--file-name", default="", type=str)

    args = parser.parse_args()

    endpoint_addr = args.remote_address
    iport = args.interactive_port
    bport = args.broadcast_port
    fileName = args.file_name

    try:
        with open(fileName, "r") as f:
            commands = f.readlines()
    except IOError:
        commands = []

    try:
        c = ComposteClient(
            "tcp://{}:{}".format(endpoint_addr, iport),
            "tcp://{}:{}".format(endpoint_addr, bport),
            StdErr,
            Encryption(),
        )
    except GenericError as e:
        print("Version mismatch: Remote server uses version {}".format(str(e)))
        sys.exit(1)

    app = QtWidgets.QApplication(sys.argv)
    app.setWindowIcon(QtGui.QIcon("assets/favicon.ico"))

    repl_funs = {
        # Supporting/Utility routines
        "register": c.register,
        "login": c.login,
        "list-projects": c.retrieve_project_listings_for,
        "create-project": c.create_project,
        "get-project": c.get_project,
        "subscribe": c.subscribe,
        "unsubscribe": c.unsubscribe,
        "share": c.share,
        # Music updates
        "change-key-signature": c.changeKeySignature,
        "insert-note": c.insertNote,
        "remove-note": c.removeNote,
        "insert-metronome-mark": c.insertMetronomeMark,
        "remove-metronome-mark": c.removeMetronomeMark,
        "transpose": c.transpose,
        "insert-clef": c.insertClef,
        "remove-clef": c.removeClef,
        "insert-measures": c.insertMeasures,
        "add-instrument": c.addInstrument,
        "remove-instrument": c.removeInstrument,
        "add-dynamic": c.addDynamic,
        "remove-dynamic": c.removeDynamic,
        "add-lyric": c.addLyric,
        # Client exclusive updates
        "start-editor": c.startEditor,
        "playback": c.playback,
        "chat": c.chat,
        "toggle-tts": c.toggleTTS,
        "tts-on": c.ttsOn,
        "tts-off": c.ttsOff,
    }

    the_worst_repl_you_will_ever_see(repl_funs, setup=commands)
    c.stop()
    sys.exit(0)
