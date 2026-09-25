"""Offline tests for AnonBox filtering (GROUP-based browse + decrypt)."""
from remailers import create_hsub
from remailers.aam import AnonBox


class FakeArticle:
    def __init__(self, text, subject=""):
        self._text = text
        self._subject = subject
        self._body = None

    @property
    def text(self):
        if self._body is not None:
            return "\n".join(b.decode("utf-8") for b in self._body)
        return self._text

    @property
    def subject(self):
        return self._subject


class FakeServer:
    def __init__(self, articles):
        self._articles = articles

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_articles(self, group, limit=50):
        return list(self._articles)


class FakeCreds:
    """Decrypts only messages containing the FOR-US marker."""

    def decrypt(self, text):
        if "FOR-US" in text:
            return "secret plan"
        raise ValueError("not encrypted to our key")


def _pgp(marker):
    return f"-----BEGIN PGP MESSAGE-----\n{marker}\n-----END PGP MESSAGE-----"


def test_retrieve_keeps_only_decryptable():
    articles = [
        FakeArticle(_pgp("FOR-US"), subject="abcd"),
        FakeArticle(_pgp("for-someone-else"), subject=" deadbeef"),
        FakeArticle("plain text, no pgp here", subject="hello"),
    ]
    box = AnonBox(FakeCreds(), FakeServer(articles))
    got = box.retrieve(limit=10)
    assert len(got) == 1
    assert got[0].text == "secret plan"


def test_retrieve_by_subject_matches_hsub():
    subject = "evil dolphin captain"
    hsub = create_hsub(subject)
    articles = [
        FakeArticle(_pgp("FOR-US"), subject=hsub),          # ours, hsub match
        FakeArticle(_pgp("FOR-US"), subject="unrelated"),   # decrypts but no match
    ]
    box = AnonBox(FakeCreds(), FakeServer(articles))
    got = box.retrieve_by_subject(subject, limit=10)
    assert len(got) == 1
    assert got[0].text == "secret plan"
