"""Scan alt.anonymous.messages and try to decrypt messages addressed to us.

Reading is anonymous; this needs no account. Only messages encrypted to our
key decrypt — everything else is skipped.
"""
from remailers.keys import Credentials
from remailers.aam import AnonBox
from usenet.server_entry import UsenetServer

USENET_URL = "news.neodome.net"   # carries alt.anonymous.messages

creds = Credentials("my_private_key.asc", name="PythonicGhost")
inbox = AnonBox(creds, UsenetServer(USENET_URL, timeout=20))

# Search by subject (matches a plaintext subject, its hSub, or eSub).
subject = "evil dolphin"
print("searching", repr(subject), "on", USENET_URL)
for article in inbox.retrieve_by_subject(subject, limit=100):
    print(article.subject, "-", article.text)

# Brute force: try to decrypt every recent PGP message in the group.
print("scanning latest messages on", USENET_URL)
for article in inbox.retrieve(limit=50):
    print(article.subject, "-", article.text)
