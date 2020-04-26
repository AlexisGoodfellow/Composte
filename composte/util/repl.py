#!/usr/bin/env python3

# This file provides what is quite possibly the world's worst REPL. Some
# docstrings are shoehorned into being used as interactive REPL help, so it
# is not possible to give them more useful docstrings. Mark, I apologize in
# advance for the pain that attempting to understand the contents of this file
# will cause you.

import re
import os, sys
import inspect
import time
import json

DEBUG = True


class SyntaxError(Exception):
    pass


def I_dont_know_what_you_want_me_to_do(*args):
    """
    Unknown command
    """
    print("Unknown command")


def _sleep(seconds):
    """
    sleep seconds

    Sleep for some number of seconds
    """
    time.sleep(int(seconds))


def _slice(start, stop, string):
    """
    slice start-index end-index string

    Extract a substring from a string
    """
    string = str(string)
    start = None if start == ":" else int(start)
    end = None if stop == ":" else int(stop)

    if start is None and end is None:
        return string
    elif start is None and end is not None:
        return string[:end]
    elif end is None and start is not None:
        return string[start:]
    else:
        return string[start:end]


hard_store = ".repl_vars"


def _export(name, value):
    """
    export name value

    Export durable variable name with given value. Persists across repl
    invocations
    """
    try:
        with open(hard_store, "r") as f:
            things = f.read()
    except FileNotFoundError:
        things = "{}"

    things = json.loads(things)
    things[name] = value
    things = json.dumps(things)

    with open(hard_store, "w") as f:
        f.write(things)

    return value


def _import(name):
    """
    import name

    Import durable variable from previous repl sessions
    """
    try:
        with open(hard_store, "r") as f:
            things = f.read()
    except FileNotFoundError:
        return ""

    things = json.loads(things)

    value = things.get(name, "")

    return value


def echo(*args):
    """
    echo [args...]

    Prints its arguments
    """
    args = [str(arg) for arg in args]
    if DEBUG:
        str_ = ", ".join(list(args))
    else:
        str_ = " ".join(args)

    return str_


class REPL_env:
    """
    Literally a wrapper around a python dictionary. Could be done better if I
    wanted to chain REPL bindings correctly, but I'm lazy and this is low
    priority.
    """

    def __init__(self):
        self.__bindings = {}

    def set(self, name, value):
        """
        set name value

        Set a variable called `name` to have value `value`
        """
        self.__bindings[name] = str(value)
        return value

    def unset(self, name):
        """
        unset name

        Unset the variable called `name`
        """
        try:
            val = self.__bindings[name]
            del self.__bindings[name]
        except KeyError as e:
            pass
        return val

    def get(self, name):
        """
        get name

        Get the value of the variable called `name`
        """
        try:
            return self.__bindings[name]
        except KeyError as e:
            return ""


class repl_source:
    __max_depth = 500

    def __init__(self, prompt):
        self.__fps = []
        self.__prompt = prompt

    def source(self, filename):
        """
        source script

        Source a script. Read the script file and interpret each line as a
        command to evaluate.
        """
        if len(self.__fps) > self.__max_depth:
            return "source: max depth ({}) exceeded: not sourcing {}".format(
                self.__max_depth, filename
            )

        try:
            fp = open(filename, "r")
        except FileNotFoundError as e:
            print(str(e))
            return None

        self.__fps.append(fp)
        return None

    def read(self):
        """
        read

        Get the next line of input from either the current sourced file or
        from standard input
        """
        if not self.__fps:
            s = input(self.__prompt()).lstrip()

        else:
            s = self.__fps[-1].readline().strip()

            # This is how readline ends in a file
            if s == "":
                # End the file's miserablbe existence
                fp = self.__fps.pop()
                fp.close()

                s = self.read()

        return s


def stop_repl_help(*args):
    """
    Stop-REPL

    End this REPL session
    """
    # Exists to provide help for a REPL builtin
    pass


def last_help(*args):
    """
    last

    Show the result of the most recently run command
    """
    # Exists to provide help for a REPL builtin
    pass


def alias_help(*args):
    """
    alias oldname newname

    Introduce newname as an alias for oldname
    """
    pass


def show_help(builtins, callbacks, fun=None, *args):
    """
    help [command]

    Display help about `command`

    External commands take precedence over builtins
    Commands prefixed with a backslash will check builtins before external
    commands
    """

    # Top level help
    if fun is None:
        fnames = callbacks.keys()
        builtins = builtins.keys()
        print(
            """help [command]

Display help about `command`. The following commands are available:
"""
        )
        for fname in fnames:
            print(fname)
        for builtin_name in builtins:
            print(builtin_name)
        return

    # Command level help

    first = callbacks
    second = builtins

    if fun[0] == "\\":
        first, second = second, first
        fun = fun[1:]

    target = first.get(fun, None)
    if target is None:
        target = second.get(fun, I_dont_know_what_you_want_me_to_do)

    doc = inspect.getdoc(target)
    print(doc)


def merge_args(args):
    """
    Merge arguments separated by escaped whitespace
    """
    new_args = []

    skip = 0
    collect = ""
    for arg in args:
        if arg is None:
            return []

        if skip > 0:
            skip = skip - 1
            if arg[-1] != "\\":
                collect = collect + " " + arg
            else:
                skip = skip + 1
                collect = collect + " " + arg[:-1]
                continue
        else:
            collect = arg

        if arg[-1] == "\\":
            skip = skip + 1
            arg = arg[:-1]
            collect = arg
            continue

        new_args.append(collect)

    if skip > 0:
        new_args.append(collect)

    return new_args


def expand_vars(env, args):
    """
    Expand variables to their contents. Unset variables expand to the empty
    string.

    For example, if the variable `hello` is set to the value "world", then
    `$hello` will be expanded to "world"
    """
    new_args = []
    for arg in args:
        if arg[0] == "$":
            arg = arg[1:]
            arg = env.get(arg)
        new_args.append(arg)

    return new_args


def split_args(args):
    new_args = []

    for arg in args:
        parts = arg.split("`")
        if len(parts) == 1:
            new_args.append(arg)
        elif len(parts) == 2:
            if parts[0] == "":
                new_args.append("`")
                if parts[1] != "":
                    new_args.append(parts[1])
            elif parts[1] == "":
                if parts[0] != "":
                    new_args.append(parts[0])
                new_args.append("`")

    return new_args


def quote(args):
    """
    Quote whitespace in arguments by escaping whitespace
    """
    new_args = []

    for arg in args:
        bits = arg.split()
        bobs = "\ ".join(bits)
        new_args.append(bobs)

    return new_args


def do_sub_repl_if_needed(
    callbacks,
    default_function=I_dont_know_what_you_want_me_to_do,
    prompt=lambda: ">>> ",
    args=None,
):
    """
    Perform command substitution if necessary. `command args` will be replaced
    with the output of evaluating `command args`.

    For example, echo `echo a` prints a
    """

    if args is None:
        return ""

    new_args = []

    sub_command = None
    sub_command_args = []

    started_subcommand = False
    for arg in args:

        if len(arg) == 0:
            if started_subcommand:
                sub_command_args.append(arg)
            elif not started_subcommand:
                new_args.append(arg)
            continue

        # Start or end a subrepl substitution
        if arg == "`":
            # New subcommand
            if not started_subcommand:
                started_subcommand = True
                sub_command = None
                sub_command_args = []
            # Finish a subcommand, so execute it
            else:
                started_subcommand = False

                # Quote arguments again
                sub_command_args = quote(sub_command_args)

                # Evaluate expression and get result
                replacement = the_worst_repl_you_will_ever_see(
                    callbacks,
                    default_function,
                    prompt,
                    once=True,
                    to_eval=[sub_command] + sub_command_args,
                )
                # Replace expression with result
                new_args.append(replacement)

            # Backticks are moved to their own separate args
            continue

        # Shunt arguments to the right places
        if started_subcommand:
            if sub_command is None:
                sub_command = arg
            else:
                sub_command_args.append(arg)
        else:
            new_args.append(arg)

    if started_subcommand:
        raise SyntaxError('Unmatched "`"')

    return new_args


def the_worst_repl_you_will_ever_see(
    callbacks,
    default_function=I_dont_know_what_you_want_me_to_do,
    prompt=lambda: ">>> ",
    once=False,
    to_eval=None,
    setup=[],
):
    """
    Start an interactive REPL backed by callbacks
    { command-name: function-to-invoke }
    REPL commands have the form COMMAND [ARGUMENTS], splitting on whitespace
    %% begins a linewise comment
    """

    env = REPL_env()
    cin = repl_source(prompt)

    # Help is an even more builtin builtin D:
    builtins = {
        "Stop-REPL": stop_repl_help,
        "help": show_help,
        "last": last_help,
        "echo": echo,
        "set": env.set,
        "unset": env.unset,
        "get": env.get,
        "sleep": _sleep,
        "slice": _slice,
        "export": _export,
        "import": _import,
        "source": cin.source,
        "alias": alias_help,
    }

    res = None
    done = False
    laps = 0
    while not done:
        if once:
            if laps > 0:
                break
            else:
                laps = laps + 1

        if to_eval is None and setup == []:
            try:
                read = cin.read()
                read = read.split("%%", 1)[0]
                if read == "":
                    continue
            except KeyboardInterrupt as e:
                break
            except EOFError as e:
                break
        elif to_eval is None:
            read = setup.pop(0)
        else:
            read = " ".join(to_eval)
            to_eval = None

        components = read.split()

        if len(components) == 0:
            continue
        else:
            command, args = components[0], components[1:]

        if command == "Stop-REPL":
            done = True
            continue

        args = merge_args(args)
        args = split_args(args)
        args = expand_vars(env, args)
        try:
            args = do_sub_repl_if_needed(callbacks, default_function, prompt, args)
        except SyntaxError as e:
            print(str(e))
            continue

        # Show help
        if command == "help":
            show_help(builtins, callbacks, *args)
            continue
        elif command == "last":
            print(str(res))
            continue
        elif command == "source":
            cin.source(args[0])
            continue
        elif command == "alias":
            # Forgive me
            def alias(oldname, newname):
                """
                alias oldname newname

                Introduce newname as an alias for oldname
                """
                if newname in callbacks:
                    return "no-override"

                if oldname in builtins:
                    oldfun = builtins[oldname]
                elif oldname in callbacks:
                    oldfun = callbacks[oldname]
                else:
                    # oldname is not a known command
                    return "bad-target"

                callbacks[newname] = oldfun
                return None

            try:
                ret = alias(*args)
            except TypeError as e:
                if str(e).startswith(alias.__name__):
                    fname, msg = str(e).split(" ", 1)
                    print("{} {}".format(command, msg))
                else:
                    print(str(e))
                continue
            if ret == "no-override":
                print("alias: cannot override existing command")
            elif ret == "bad-target":
                print("alias: cannot alias to non-command")
            continue

        # Actually do something

        exec_ = callbacks.get(command, default_function)
        first = callbacks
        second = builtins

        if command[0] == "\\":
            first, second = second, first
            command = command[1:]

        target = first.get(command, None)
        if target is None:
            target = second.get(command, default_function)

        exec_ = target

        try:
            res = exec_(*args)
        except TypeError as e:
            if str(e).startswith(exec_.__name__):
                fname, msg = str(e).split(" ", 1)
                print("{} {}".format(command, msg))
            else:
                print(str(e))
            continue

        if res is not None and not once:
            print(str(res))
        if res is not None:
            res = str(res)

    return res
