# AnonBox: Anonymous Usenet Messaging

Post and retrieve anonymous messages in `alt.anonymous.messages` with PGP
encryption.

## Overview

`AnonBox` encrypts messages with PGP, posts them to Usenet under a hashed or
plain subject, and later retrieves messages addressed to you — decrypting them
with your private key. It browses the group by article range (GROUP), which
works on public servers even where `NEWNEWS` is disabled.

## Servers

Reading `alt.anonymous.messages` is anonymous on many servers (e.g.
`news.neodome.net`). Posting needs a server that accepts anonymous posts;
`paganini.bofh.team` and `news.tcpreset.net` do (no account) and carry the
group. See [servers](../../usenet/docs/servers.md) and `usenet.probe`.

## Basic usage

```python
from usenet import UsenetServer
from remailers import Credentials, AnonBox

creds = Credentials("anon.asc", name="PythonicAnon")
inbox = AnonBox(creds, UsenetServer("news.neodome.net"))

# Pull the latest messages and keep the ones encrypted to us
for article in inbox.retrieve(limit=50):
    print(article.text)   # already decrypted
```

## Posting a message

Encrypt and post under an hSub:

```python
from usenet import UsenetServer
from remailers import Credentials, create_hsub

creds = Credentials("anon.asc")
hsub = create_hsub("secret meeting")
ciphertext = creds.encrypt("Meet at the old mill at 3 PM")

with UsenetServer("paganini.bofh.team") as server:
    print(server.post(ciphertext, hsub, "alt.anonymous.messages"))
```

## Retrieving messages

### By subject

```python
inbox = AnonBox(creds, UsenetServer("news.neodome.net"))

articles = inbox.retrieve_by_subject(
    "secret meeting",
    limit=200,    # how many recent messages to scan
    hsubs=True,   # match hashed subjects
    esubs=False,  # match encrypted subjects (needs esub_key)
)
for article in articles:
    print(article.author, article.date)
    print(article.text)   # decrypted
```

Parameters:
- `subject` — the plaintext subject to match
- `limit` — number of recent messages to scan (default 200)
- `hsubs=True` — match hashed subjects (hSub)
- `esubs=True` — match encrypted subjects (eSub; requires `esub_key`)

### All messages

```python
articles = inbox.retrieve(limit=50)
```

Only messages containing `BEGIN PGP MESSAGE` that decrypt with your key are
returned; everything else is skipped.

### With eSub

```python
inbox = AnonBox(creds, server, esub_key="shared-secret")
articles = inbox.retrieve_by_subject("message code", esubs=True, hsubs=False)
```

Subject matching is tried in order:
1. exact plaintext match (`subject == article.subject`)
2. hSub match (if `hsubs=True`)
3. eSub match (if `esubs=True` and `esub_key` is set)

## Group

`AnonBox` always uses `alt.anonymous.messages`:

```python
print(AnonBox.GROUP)   # 'alt.anonymous.messages'
```

## Notes

- Messages that fail PGP decryption (not for your key, not a PGP message,
  corrupted) are silently skipped.
- `AnonBox` and `UsenetServer` are not thread-safe; use one instance per thread.
- A larger `limit` scans further back but costs one head+body fetch per message.

## Example workflow

```python
from usenet import UsenetServer
from remailers import Credentials, AnonBox, create_hsub

creds = Credentials("anon.asc", name="SecretAgent")

# Send
hsub = create_hsub("rendezvous-alpha")
ciphertext = creds.encrypt("Call me at the usual place")
with UsenetServer("paganini.bofh.team") as srv:
    srv.post(ciphertext, hsub, "alt.anonymous.messages")

# Check for replies under the same code word
inbox = AnonBox(creds, UsenetServer("news.neodome.net"))
for article in inbox.retrieve_by_subject("rendezvous-alpha", limit=200):
    print(article.date, article.text)
```
