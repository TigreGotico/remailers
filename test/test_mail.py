"""Offline tests for RFC-822 message framing."""
from remailers.mail import build_message


def test_headers_are_not_indented():
    msg = build_message("me@example.com", ["you@example.com"], "hi", "body")
    for line in msg.split("\r\n"):
        if line.startswith(("From:", "To:", "Subject:")):
            assert not line[0].isspace()


def test_message_structure():
    msg = build_message("me@example.com", ["a@x.com", "b@x.com"], "subj", "hello")
    assert msg.startswith("From: me@example.com\r\n")
    assert "To: a@x.com, b@x.com\r\n" in msg
    assert "Subject: subj\r\n" in msg
    # blank line separates headers from body
    head, _, body = msg.partition("\r\n\r\n")
    assert body.strip() == "hello"
