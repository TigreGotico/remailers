import os


def generate_iv(length=8):
    """Return a cryptographically random initialization vector.

    `length` is in bytes (8 by default — one Blowfish block / the hSub IV size).
    """
    return os.urandom(length)
