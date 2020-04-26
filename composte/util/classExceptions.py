"""
A module of exceptions for creating more readable abstract classes.  Python's
built-in ABC functionality added unnecessary levels of complexity to the code
(in large part because of the multiple-inheritance it introduced), so we decided
to not use it.
"""


class VirtualMethodError(NotImplementedError):
    """Raise in methods meant to be abstract methods when they are called."""


def virtualmethod(fun):
    def virt(self, *args, **kwargs):
        raise VirtualMethodError(type(self).__name__ + "." + fun.__name__)

    return virt
