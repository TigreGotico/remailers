# remailers

A toolkit for **anonymous messaging** with PGP over Usenet and Tor email:
hashed/encrypted subjects (hSub/eSub), nym-server (ZAX) registration, and
SOCKS/Tor SMTP. Built on top of [`usenet`](https://github.com/JarbasAl/usenet).

> For research and privacy education. The public nym/remailer network is largely
> historical; treat the bundled server definitions as starting points.

## Install

```bash
pip install remailers
```

## Quickstart

Generate (or load) a PGP identity:

```python
from remailers import Credentials

creds = Credentials("my_key.asc", name="PythonicAnon")
print(creds.pubkey)
```

Hashed and encrypted subjects — let a recipient spot a message meant for them
without revealing the subject:

```python
from remailers import create_hsub, match_hsub, create_esub, match_esub

hsub = create_hsub("evil dolphin captain")
assert match_hsub(hsub, "evil dolphin captain")

esub = create_esub("evil dolphin captain", key="shared-secret")
assert match_esub("evil dolphin captain", "shared-secret", esub)
```

Post and retrieve anonymous messages via `alt.anonymous.messages`:

```python
from usenet import UsenetServer
from remailers import Credentials, AnonBox, create_hsub

creds = Credentials("my_key.asc")
hsub = create_hsub("evil dolphin captain")
ciphertext = creds.encrypt("meet at noon")

with UsenetServer("news.neodome.net") as server:
    server.post(ciphertext, hsub, "alt.anonymous.messages")

inbox = AnonBox(creds, UsenetServer("news.neodome.net"))
for article in inbox.retrieve_by_subject("evil dolphin captain"):
    print(article.text)
```

ZAX nym servers and Tor email are in `remailers.zax` and `remailers.mail`; see
`examples/`.

## Security notes

- Initialization vectors come from `os.urandom` (`remailers.utils.generate_iv`).
- hSub uses SHA-256; eSub uses Blowfish (Type-I compatibility) — eSub exists for
  interop with the legacy remailer ecosystem, not as modern AEAD.
- Message bodies are protected by PGP (RSA-4096, AES-256), not by the subject
  scheme.

## Testing

```bash
pip install -e .[test]
pytest test/
```

Tests are offline — subject round-trips, IV entropy, and a PGP encrypt/decrypt
cycle with a freshly generated key.

## License

Apache-2.0
