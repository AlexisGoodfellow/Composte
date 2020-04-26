import music21

import ComposteClient

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from client.gui import UINote, UIClef, UITimeSignature, UIKeySignature
from client.gui.UIScoreViewport import UIScoreViewport


class Editor(QtWidgets.QMainWindow):

    """
    The main GUI for editing Composte projects.
    """

    ## For looking up note types from commands in the debug console.
    __noteTypeLookup = {
        "whole": UINote.UINote_Whole,
        "half": UINote.UINote_Half,
        "quarter": UINote.UINote_Quarter,
        "eighth": UINote.UINote_Eighth,
        "8th": UINote.UINote_Eighth,
        "sixteenth": UINote.UINote_16th,
        "16th": UINote.UINote_16th,
        "half.": UINote.UINote_Half_Dotted,
        "quarter.": UINote.UINote_Quarter_Dotted,
        "eighth.": UINote.UINote_Eighth_Dotted,
        "8th.": UINote.UINote_Eighth_Dotted,
        "sixteenth.": UINote.UINote_16th_Dotted,
        "16th.": UINote.UINote_16th_Dotted,
    }
    __defaultClef = UIClef.treble()
    __defaultTimeSignature = UITimeSignature.UITimeSignature(4, 4)
    __defaultKeySignature = UIKeySignature.C()

    def __init__(self, client: ComposteClient.ComposteClient, *args, **kwargs):
        """
        Start a new editor, working on the projected loaded by client.

        :param client: a Composte client, which manages updates to the project.
        """
        super(Editor, self).__init__(*args, **kwargs)
        self.__client = client
        self.__makeUI()
        self.__resetAll()
        self.__client._updateGUI.connect(self.update)
        self.__client._chatToGUI.connect(self.printChatMessage)

    def update(self, startOffset: float, endOffset: float):
        """
        Update a section of the score on the UI from the copy held by the
        client.

        :note: Updating sections is not currently supported; all updates redraw
        the entire score.

        :param startOffset: First quarter-note offset to be updated.  If None,
            update from start of project.
        :param startOffset: Quarter-note offset after the last one to be
            updated.  If None, update through end of project.
        """
        ## FIXME: Updating of specific sections not working quite yet.
        try:
            self.__ui_scoreViewport.update(self.__client.project(), None, None)
        except ValueError as e:
            self.__debugConsoleWrite(str(e))

    def __resetAll(self):
        """
        Reload the entire project from the Composte client, and redraw
        everything.
        """
        self.update(None, None)

    def __makeUI(self):
        """
        Construct the main UI.
        """
        self.__ui_mainSplitter = QtWidgets.QSplitter(Qt.Vertical, self)

        self.__ui_scoreViewport = UIScoreViewport(parent=self.__ui_mainSplitter)

        # For some reason this string can't be blank, but it can be anything
        # else that isn't a font.
        self.__ui_debugConsole_font = QtGui.QFont("nothing")
        self.__ui_debugConsole_font.setStyleHint(QtGui.QFont.Monospace)

        self.__ui_debugConsole_layoutWidget = QtWidgets.QWidget(self.__ui_mainSplitter)
        self.__ui_debugConsole_layout = QtWidgets.QVBoxLayout(
            self.__ui_debugConsole_layoutWidget
        )
        self.__ui_debugConsole_layoutWidget.setLayout(self.__ui_debugConsole_layout)
        self.__ui_debugConsole_log = QtWidgets.QTextEdit(
            self.__ui_debugConsole_layoutWidget
        )
        self.__ui_debugConsole_log.setReadOnly(True)
        self.__ui_debugConsole_log.setFont(self.__ui_debugConsole_font)
        self.__ui_debugConsole_input = QtWidgets.QLineEdit(
            self.__ui_debugConsole_layoutWidget
        )
        self.__ui_debugConsole_input.setFont(self.__ui_debugConsole_font)
        self.__ui_debugConsole_input.returnPressed.connect(self.__processDebugInput)
        self.__ui_debugConsole_layout.addWidget(self.__ui_debugConsole_log)
        self.__ui_debugConsole_layout.addWidget(self.__ui_debugConsole_input)
        self.__ui_debugConsole_layoutWidget.hide()

        self.__ui_mainSplitter.addWidget(self.__ui_scoreViewport)
        self.__ui_mainSplitter.addWidget(self.__ui_debugConsole_layoutWidget)

        # Make the debug console not take up most of the window.
        self.__ui_mainSplitter.setStretchFactor(0, 3)

        self.setCentralWidget(self.__ui_mainSplitter)

        self.__makeMenuBar()
        self.__makeToolbar()

    def __makeMenuBar(self):
        """
        Construct the menu bar.
        """
        self.__ui_filemenu = QtWidgets.QMenu("File", parent=self)
        self.__ui_editmenu = QtWidgets.QMenu("Edit", parent=self)

        self.__ui_act_debugConsole = self.__ui_filemenu.addAction(
            "Debug Console Enabled"
        )
        self.__ui_act_debugConsole.setCheckable(True)
        self.__ui_act_debugConsole.setShortcut(QtGui.QKeySequence(Qt.Key_Escape))
        self.__ui_act_debugConsole.changed.connect(self.__toggleDebug)

        self.__ui_act_quit = self.__ui_filemenu.addAction("Quit")
        self.__ui_act_quit.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        self.__ui_act_quit.triggered.connect(self.closeEvent)

        self.__ui_act_edit = self.__ui_editmenu.addAction("Play")
        self.__ui_act_edit.setShortcut(QtGui.QKeySequence("Ctrl+space"))
        self.__ui_act_edit.triggered.connect(self.__handlePlay)

        self.__ui_menubar = QtWidgets.QMenuBar(parent=self)
        self.__ui_menubar.addMenu(self.__ui_filemenu)
        self.__ui_menubar.addMenu(self.__ui_editmenu)

        self.setMenuBar(self.__ui_menubar)

    def closeEvent(self, ev):
        """
        Gracefully disconnect from the Composte client and exit.
        """
        # Tell the client we are disconnecting
        self.__client.closeEditor()
        # Remove the reference loop between the client and the editor, to avoid
        # garbage collection issues.
        self.__client = None
        self.deleteLater()

    def __makeToolbar(self):
        """
        Build the toolbar.

        :note: Not implemented yet.
        """
        pass

    def printChatMessage(self, msg):
        """
        Display a chat message to the debug console.
        """
        self.__debugConsoleWrite(msg)

    def __debugConsoleWrite(self, msg):
        """
        Display a message in the debug console.
        """
        self.__ui_debugConsole_log.append(msg)

    def __toggleDebug(self):
        """
        Show/hide the debug console.
        """
        self.__ui_debugConsole_layoutWidget.setVisible(
            self.__ui_act_debugConsole.isChecked()
        )
        if self.__ui_act_debugConsole.isChecked():
            self.__ui_debugConsole_input.setFocus()

    def __debugConsoleHelp(self, fn=None):
        """
        Print a help message to the debug console.

        :param fn: If None, print help for all commands.  If it is a command,
            print just the help for that command.
        """
        if fn is None:
            msg = (
                "help/?       --  Display this help message\n"
                "CMD1 ; CMD2  --  Execute CMD1 followed by CMD2"
            )
            self.__debugConsoleWrite(msg)
        if fn == "clear" or fn is None:
            msg = "clear        --  Clear the debug console history"
            self.__debugConsoleWrite(msg)
        if fn == "ttson" or fn is None:
            msg = (
                "ttson        --  Enable text-to-speech for chat messages, "
                "if available."
            )
            self.__debugConsoleWrite(msg)
        if fn == "ttsoff" or fn is None:
            msg = "ttsoff       --  Disable text-to-speech for chat messages."
            self.__debugConsoleWrite(msg)
        if fn == "play" or fn is None:
            msg = (
                "play/p [PART_INDEX]\n"
                "    Play back the part specified by the given index, "
                "or part 0 if none is specified."
            )
            self.__debugConsoleWrite(msg)
        if fn == "chat" or fn is None:
            msg = (
                "chat/c MESSAGE\n"
                "    Send MESSAGE (which may contain spaces, but not "
                "    semicolons) to all users\n working on the current "
                "    project"
            )
            self.__debugConsoleWrite(msg)
        if fn == "insert" or fn is None:
            msg = (
                "insert/i PART_INDEX PITCH NOTE_TYPE OFFSET\n"
                "    Insert a NOTE_TYPE into the indicated part, at \n"
                "    quarter-note-offset OFFSET and with the given PITCH"
            )
            self.__debugConsoleWrite(msg)
        if fn == "delete" or fn is None:
            msg = (
                "delete/d PART_INDEX PITCH OFFSET\n"
                "    Remove the note in the indicated part at\n"
                "    quarter-note-offset OFFSET and pitch PITCH"
            )
            self.__debugConsoleWrite(msg)

    def __handleAddPart(self, clef):
        """
        Insert a new part. Not currently implemented.
        """
        raise NotImplementedError

    def __handlePlay(self, part=0):
        """
        Tell the Composte client to play back the given part.
        """
        self.__client.playback(part)

    def __handleAddLine(self):
        """
        Add a line to the display.  Now largely unused, as the display will
        expand automatically when notes are added.  Purely a local change, which
        does not affect the actual score at all.
        """
        self.__ui_scoreViewport.addLine()

    def __handleInsertNote(
        self, partIdx: int, pitch: music21.pitch.Pitch, ntype, offset: float
    ):
        """
        Tell the Composte client to insert a note into the current project.

        :param partIdx: Index of the part to be inserted into.
        :param pitch: Pitch of the note to be inserted, as a Music21 Pitch.
        :param ntype: Note type to be inserted; must be a class which is a
            subclass of UINote, not a class instance.
        :param offset: Offset (in quarterlengths) from the beginning of the
            piece at which the note should be inserted.
        """
        self.__client.insertNote(
            self.__client.project().projectID,
            offset,
            partIdx,
            str(pitch),
            ntype.length(),
        )

    def __handleDeleteNote(
        self, partIdx: int, pitch: music21.pitch.Pitch, offset: float
    ):
        """
        Tell the Composte client to remove a note from the current project.

        :param partIdx: Index of the part to be removed from.
        :param pitch: Pitch of the note to be removed, as a Music21 Pitch.
        :param offset: Offset (in quarterlengths) from the beginning of the
            piece of the note to be removed.
        """
        self.__client.removeNote(
            self.__client.project().projectID, offset, partIdx, str(pitch)
        )

    def __handleChatMessage(self, name, msg):
        """
        Tell the Composte client to send out a chat message.

        :param name: The username to be displayed with the message.
        :param msg: The message to be broadcast.
        """
        self.__client.chat(self.__client.project().projectID, name, msg)

    def __handleTTSon(self):
        """
        Tell the Composte client to enable text-to-speech, if available.
        """
        self.__client.ttsOn()

    def __handleTTSoff(self):
        """
        Tell the Composte client to disable text-to-speech.
        """
        self.__client.ttsOff()

    def __processDebugInput(self):
        """
        Handle a line of input from the debug console.
        """
        text = self.__ui_debugConsole_input.text()
        self.__ui_debugConsole_input.clear()
        if not text:
            return
        cmdstrs = map(str.strip, text.split(";"))
        for cmdstr in cmdstrs:
            self.__processDebugCommand(cmdstr)

    def __processDebugCommand(self, cmdstr):
        """
        Handle a single command from the debug console.

        :param cmdstr: The command to be executed, as an unparsed string.
        """
        args = cmdstr.split(" ")
        cmd = args[0].lower()
        args.pop(0)

        if cmd in ["clear"]:
            self.__ui_debugConsole_log.clear()
        elif cmd in ["chat", "c"]:
            if len(args) == 0:
                self.__debugConsoleHelp("chat")
            name = args[0]
            self.__handleChatMessage(name, " ".join(args[1:]))
        elif cmd in ["ttson"]:
            self.__handleTTSon()
        elif cmd in ["ttsoff"]:
            self.__handleTTSoff()
        elif cmd in ["play", "p"]:
            if len(args) == 0:
                self.__handlePlay()
            if len(args) == 1:
                try:
                    partIdx = int(args[0])
                except ValueError:
                    msg = "Unable to generate part index from '" + args[1] + "'"
                    self.__debugConsoleWrite(msg)
                    return
                self.__handlePlay(partIdx)
            else:
                self.__debugConsoleHelp("play")
        ## NOT CURRENTLY SUPPORTED
        # elif cmd in ['addpart']:
        #     self.__handleAddPart(self.__defaultClef)
        elif cmd in ["addline"]:
            self.__handleAddLine()
        elif cmd in ["insert", "i"]:
            if len(args) != 4:
                self.__debugConsoleHelp("insert")
                return

            try:
                partIdx = int(args[0])
            except ValueError:
                msg = "Unable to generate part index from '" + args[1] + "'"
                self.__debugConsoleWrite(msg)

            try:
                pitch = music21.pitch.Pitch(args[1])
            except music21.pitch.PitchException:
                msg = "Unable to generate pitch from '" + args[1] + "'"
                self.__debugConsoleWrite(msg)
                return

            if args[2].lower() in Editor.__noteTypeLookup:
                ntype = Editor.__noteTypeLookup[args[2].lower()]
            else:
                msg = "Unknown note type '" + args[2] + "'"
                self.__debugConsoleWrite(msg)
                return

            try:
                offset = float(args[3])
            except ValueError:
                msg = "Unable to generate time offset from '" + args[3] + "'"
                self.__debugConsoleWrite(msg)
                return

            self.__handleInsertNote(partIdx, pitch, ntype, offset)
        elif cmd in ["delete", "d"]:
            if len(args) != 3:
                self.__debugConsoleHelp("delete")
                return

            try:
                partIdx = int(args[0])
            except ValueError:
                msg = "Unable to generate part index from '" + args[1] + "'"
                self.__debugConsoleWrite(msg)
                return

            try:
                pitch = music21.pitch.Pitch(args[1])
            except music21.pitch.PitchException:
                msg = "Unable to generate pitch from '" + args[1] + "'"
                self.__debugConsoleWrite(msg)
                return

            try:
                offset = float(args[2])
            except ValueError:
                msg = "Unable to generate time offset from '" + args[2] + "'"
                self.__debugConsoleWrite(msg)
                return

            self.__handleDeleteNote(partIdx, pitch, offset)
        else:
            self.__debugConsoleHelp()
