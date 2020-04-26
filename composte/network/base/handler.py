class Stateful:
    def __init__(self, handler, state):
        """
    [UNTESTED and UNUSED]
    A stateful handler for network endpoints. Not necessary for any technical
    reasons, but the pattern may be familiar.

    handler must be callable in the following fashion:
        handler(message, state)
    handler must return the following:
        (result, new_state)
        """
        self.__handler = handler
        self.__state = state

        def __call__(self, server, message):
            (res, new_state) = self.__handler(message, server, self.__state)
            self.__state = new_state
            return res
