from passlib.hash import pbkdf2_sha256


def hash(hashable):
    """
    Create a hash
    """
    record = pbkdf2_sha256.hash(hashable)

    return record


def verify(candidate, record):
    """
    Verify candidate against record
    """
    return pbkdf2_sha256.verify(candidate, record)
