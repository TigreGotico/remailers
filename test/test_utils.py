"""Offline tests for the IV generator."""
from remailers.utils import generate_iv


def test_iv_is_bytes_of_requested_length():
    iv = generate_iv(8)
    assert isinstance(iv, bytes)
    assert len(iv) == 8


def test_iv_default_length():
    assert len(generate_iv()) == 8


def test_iv_is_random():
    # cryptographic IVs must not repeat
    assert generate_iv(16) != generate_iv(16)
