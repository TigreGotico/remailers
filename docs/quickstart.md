# Quickstart

Get up and running with anonymous messaging in five minutes.

## Generate a PGP identity

Create a new key or load an existing one:

```python
from remailers import Credentials

# Creates a new key and saves it to my_key.asc
creds = Credentials("my_key.asc", name="PythonicAnon")
print(creds.pubkey)

# Later, load the same key
creds = Credentials("my_key.asc")
```

The key is generated as RSA-4096 with AES-256 encryption. If the file exists, it is loaded; if not, a new key is generated and saved.

## Hash a subject

Hide the subject with a one-way hash (hSub):

```python
from remailers import create_hsub, match_hsub

# Create an hSub
hsub = create_hsub("meeting at noon")
print(hsub)

# Later, a recipient matching against the same subject will get True
assert match_hsub(hsub, "meeting at noon")

# A different subject won't match
assert not match_hsub(hsub, "meeting at two")
```

hSub uses SHA-256 with an 8-byte initialization vector. Only someone with the plaintext subject can match it.

## Encrypt a subject (legacy)

For interop with the Type-I remailer ecosystem, use eSub (Blowfish-based):

```python
from remailers import create_esub, match_esub

# Both parties share a secret key
key = "my-shared-secret"

# Create an eSub
esub = create_esub("message code", key=key)
print(esub)

# Match it later
assert match_esub("message code", key, esub)

# Different key won't match
assert not match_esub("message code", "wrong-key", esub)
```

eSub is maintained for historical compatibility; hSub is preferred for new code.

## Post and retrieve anonymous messages

Encrypt a message with PGP and post it to `alt.anonymous.messages`:

```python
from usenet import UsenetServer
from remailers import Credentials, AnonBox, create_hsub

# Generate a key
creds = Credentials("anon.asc", name="PythonicAnon")
hsub = create_hsub("secret rendezvous")
ciphertext = creds.encrypt("Meet at the old mill")

# Post to Usenet
with UsenetServer("news.eternal-september.org") as server:
    server.post(ciphertext, subject=hsub, group="alt.anonymous.messages")

# Retrieve later
inbox = AnonBox(creds, UsenetServer("news.eternal-september.org"))
for article in inbox.retrieve_by_subject("secret rendezvous"):
    print(article.text)
```

## Send email via Tor

Send anonymous email through a Tor SOCKS proxy:

```python
from remailers.mail import send_tor_email

# Requires a local Tor SOCKS5 proxy on 127.0.0.1:9050
send_tor_email(
    user="anon@mail.smtp2go.com",
    pswd="app-password",
    destinatary="recipient@example.org",
    subject="Anonymous message",
    contents="Message body"
)
```

## Next steps

- Learn about [generating and managing PGP keys](identities.md).
- Understand [hSub vs eSub subject hiding](subjects.md).
- Post to `alt.anonymous.messages` with [AnonBox](anonbox.md).
- Configure [Tor email delivery](tor-email.md).
- See [security notes](security.md) on cryptography and threat model.

---
[Home](index.md) · [Identities →](identities.md)
