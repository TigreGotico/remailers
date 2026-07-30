"""Tests for the GnuPG backend (skipped when gpg is unavailable)."""
import pytest

from remailers.cypherpunk import build_chain
from remailers.gpg import GPGKeyring, gpg_available
from remailers.keys import Credentials

pytestmark = pytest.mark.skipif(not gpg_available(), reason="gpg not installed")

EMAIL = "gpgtest@example.com"


@pytest.fixture(scope="module")
def creds(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("gpg") / "id.asc")
    return Credentials(path, name="GpgTestKey", email=EMAIL)


def test_import_and_recipients(creds):
    with GPGKeyring(creds.pubkey) as gpg:
        assert EMAIL in gpg.recipients()


def test_gpg_encrypt_roundtrips_to_pgpy(creds):
    """gpg encrypts to our imported RSA key; PGPy decrypts it back."""
    with GPGKeyring(creds.pubkey) as gpg:
        ciphertext = gpg.encrypt(EMAIL, "secret over gpg")
    assert "BEGIN PGP MESSAGE" in ciphertext
    assert creds.decrypt(ciphertext) == "secret over gpg"


def test_build_chain_with_gpg_encryptor(creds):
    """build_chain accepts gpg.encrypt and a single-hop onion decrypts back."""
    with GPGKeyring(creds.pubkey) as gpg:
        msg, entry = build_chain([(EMAIL, EMAIL)],
                                 anon_post_to="alt.test", body="payload",
                                 encrypt=gpg.encrypt)
    assert entry == EMAIL
    assert msg.startswith("::\nEncrypted: PGP\n\n")
    inner = creds.decrypt(msg.split("\n\n", 1)[1])
    assert "Anon-Post-To: alt.test" in inner
    assert inner.strip().endswith("payload")
