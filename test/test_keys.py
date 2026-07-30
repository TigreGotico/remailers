"""Offline tests for PGP key handling (one keygen per module — RSA-4096)."""
import os

import pytest

from remailers.keys import Credentials


@pytest.fixture(scope="module")
def creds(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("keys") / "id.asc")
    return Credentials(path, name="TestNym")


def test_pubkey_exported(creds):
    assert "BEGIN PGP PUBLIC KEY BLOCK" in creds.pubkey


def test_key_file_written(tmp_path):
    path = str(tmp_path / "written.asc")
    Credentials(path, name="Writer")
    assert os.path.isfile(path)
    with open(path) as f:
        assert "BEGIN PGP PRIVATE KEY BLOCK" in f.read()


def test_key_file_roundtrips(tmp_path):
    path = str(tmp_path / "id.asc")
    first = Credentials(path, name="RoundTrip")
    # second construction loads the same key off disk, not a fresh one
    second = Credentials(path)
    assert first.pubkey == second.pubkey


def test_encrypt_decrypt_round_trip(creds):
    secret = "meet at noon, dolphin"
    ciphertext = creds.encrypt(secret)
    assert "BEGIN PGP MESSAGE" in ciphertext
    assert creds.decrypt(ciphertext) == secret
