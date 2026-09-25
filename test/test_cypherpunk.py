"""Offline tests for Type-I (Cypherpunk) message assembly."""
import pytest

from remailers.cypherpunk import build_chain, final_request, wrap_encrypted
from remailers.keys import Credentials


@pytest.fixture(scope="module")
def creds(tmp_path_factory):
    path = str(tmp_path_factory.mktemp("cpunk") / "id.asc")
    return Credentials(path, name="RemailerKey")


def test_final_request_post():
    block = final_request(anon_post_to="alt.test", body="hello")
    assert block.startswith("::\n")
    assert "Anon-Post-To: alt.test" in block
    assert block.endswith("hello")


def test_final_request_to_with_latent():
    block = final_request(dest="bob@example.com", latent="+0:30", body="hi")
    assert "Anon-To: bob@example.com" in block
    assert "Latent-Time: +0:30" in block


def test_final_request_requires_target():
    with pytest.raises(ValueError):
        final_request(body="orphan")


def test_wrap_encrypted_is_pasting_token(creds):
    wrapped = wrap_encrypted(creds.private_key.pubkey, "::\nAnon-To: x@y\n\nbody")
    assert wrapped.startswith("::\nEncrypted: PGP\n\n")
    assert "BEGIN PGP MESSAGE" in wrapped


def test_single_hop_round_trip(creds):
    key = creds.private_key.pubkey
    msg, entry = build_chain([("exit@r.org", key)],
                             anon_post_to="alt.anonymous.messages", body="secret")
    assert entry == "exit@r.org"
    assert msg.startswith("::\nEncrypted: PGP\n\n")
    # the exit remailer decrypts the inner block
    pgp = msg.split("\n\n", 1)[1]
    inner = creds.decrypt(pgp)
    assert "Anon-Post-To: alt.anonymous.messages" in inner
    assert inner.strip().endswith("secret")


def test_two_hop_onion(creds):
    key = creds.private_key.pubkey
    hops = [("entry@a.org", key), ("exit@b.org", key)]
    msg, entry = build_chain(hops, dest="bob@example.com", body="payload")
    assert entry == "entry@a.org"
    # peel the entry layer -> instructions to relay to the exit hop
    outer = creds.decrypt(msg.split("\n\n", 1)[1])
    assert "Anon-To: exit@b.org" in outer
    # the rest of the entry payload is the encrypted block for the exit hop
    inner_block = outer.split("\n\n", 1)[1]
    assert inner_block.startswith("::\nEncrypted: PGP")
    final = creds.decrypt(inner_block.split("\n\n", 1)[1])
    assert "Anon-To: bob@example.com" in final
    assert final.strip().endswith("payload")


def test_build_chain_requires_hops():
    with pytest.raises(ValueError):
        build_chain([], dest="x@y")
