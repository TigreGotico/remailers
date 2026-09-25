"""Offline tests for hSub (hashed) and eSub (encrypted) subjects."""
from remailers import create_esub, create_hsub, match_esub, match_hsub


def test_hsub_round_trip():
    subject = "captain dolphin"
    hsub = create_hsub(subject)
    assert match_hsub(hsub, subject)


def test_hsub_rejects_wrong_subject():
    hsub = create_hsub("captain dolphin")
    assert not match_hsub(hsub, "something else")


def test_hsub_length_bounds():
    # below 48 hex digits and above 80 are rejected outright
    assert not match_hsub("a" * 10, "x")
    assert not match_hsub("a" * 100, "x")


def test_esub_round_trip():
    key = "shared-secret"
    subject = "evil dolphin captain"
    esub = create_esub(subject, key)
    assert len(esub) == 48
    assert match_esub(subject, key, esub)


def test_esub_rejects_wrong_key():
    esub = create_esub("evil dolphin captain", "shared-secret")
    assert not match_esub("evil dolphin captain", "other-secret", esub)


def test_esub_random_iv_each_time():
    a = create_esub("subj", "key")
    b = create_esub("subj", "key")
    # different IV -> different ciphertext, both still match
    assert a != b
    assert match_esub("subj", "key", a)
    assert match_esub("subj", "key", b)
