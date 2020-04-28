"""Composte network exceptions."""


class ComposteBaseException(Exception):
    """Base exception. Never throw directly."""


class DecryptError(ComposteBaseException):
    """Exception for decryption failures."""


class EncryptError(ComposteBaseException):
    """Exception for encryption failures."""


class GenericError(ComposteBaseException):
    """Catch-all exception."""
