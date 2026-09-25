# API Reference

Quick lookup for all public symbols.

## Credentials

```python
from remailers import Credentials

creds = Credentials(path, name=None, email=None, expires=None)
```

PGP key management for encryption, decryption, and signing.

### Constructor

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `path` | str | - | File path to key (loaded if exists, else generated) |
| `name` | str or None | None | UID name for new key |
| `email` | str or None | None | Email for UID (optional) |
| `expires` | timedelta/datetime or None | None | Key expiry (optional) |

### Properties

| Property | Type | Description |
| --- | --- | --- |
| `pubkey` | str | Public key (ASCII-armored) |
| `private_key` | pgpy.PGPKey | Underlying PGP key object |

### Methods: encrypt, decrypt, sign

| Method | Signature | Returns | Description |
| --- | --- | --- | --- |
| `encrypt(txt, key=None)` | `encrypt(txt, key=None) -> str` | str | Encrypt plaintext (to own pubkey by default) |
| `decrypt(encrypted_message)` | `decrypt(encrypted_message) -> str` | str | Decrypt PGP message |
| `sign(message, intended_recipients=None)` | `sign(...) -> PGPSignature` | PGPSignature | Sign a message |

### Methods: key loading

| Method | Signature | Returns | Description |
| --- | --- | --- | --- |
| `load_private(path, binary=False)` | instance | None | Load key from file |
| `import_key(key_blob)` | static | pgpy.PGPKey | Load key from bytes/string |

## Subject hiding: hSub

```python
from remailers import create_hsub, match_hsub

hsub = create_hsub(text, iv=None, hsublen=48)
match_hsub(hsub, subject) -> bool
```

### create_hsub

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `text` | str | - | Subject text to hash |
| `iv` | bytes or None | None | 8-byte IV (generated if None) |
| `hsublen` | int | 48 | Output length in hex chars (48-80) |

Returns: 48 hex characters by default (192 bits: 64-bit IV + 128-bit SHA256).

### match_hsub

| Parameter | Type | Description |
| --- | --- | --- |
| `hsub` | str | hSub to test (48-80 hex chars) |
| `subject` | str | Plaintext subject to match |

Returns: `True` if hSub matches subject (with extracted IV), `False` otherwise.

## Subject hiding: eSub

```python
from remailers import create_esub, match_esub

esub = create_esub(text, key, iv=None)
match_esub(text, key, esub) -> bool
```

### create_esub

| Parameter | Type | Default | Description |
| --- | --- | --- | --- |
| `text` | str | - | Subject text |
| `key` | str | - | Shared secret (key) |
| `iv` | bytes or None | None | 8-byte IV (generated if None) |

Returns: 48 hex characters (192 bits: 64-bit IV + 128-bit Blowfish-CFB ciphertext).

### match_esub

| Parameter | Type | Description |
| --- | --- | --- |
| `text` | str | Plaintext subject |
| `key` | str | Shared secret (key) |
| `esub` | str | eSub to test (must be exactly 48 hex chars) |

Returns: `True` if eSub decrypts to text with the given key, `False` otherwise.

## AnonBox

```python
from remailers import AnonBox

inbox = AnonBox(creds, usenet_server, esub_key=None)
```

Retrieve and post anonymous messages in `alt.anonymous.messages`.

### Constructor

| Parameter | Type | Description |
| --- | --- | --- |
| `creds` | Credentials | Your PGP credentials |
| `usenet_server` | UsenetServer | Connection to NNTP server |
| `esub_key` | str or None | Shared secret for eSub matching (optional) |

### Methods

| Method | Signature | Returns | Description |
| --- | --- | --- | --- |
| `retrieve(limit=50)` | `retrieve(limit=50) -> list[Article]` | list | Decryptable messages among the latest `limit` |
| `retrieve_by_subject(subject, limit=200, esubs=True, hsubs=True)` | `-> list[Article]` | list | Messages matching subject (plain/hSub/eSub) |

### Class attributes

| Attribute | Type | Value |
| --- | --- | --- |
| `GROUP` | str | `'alt.anonymous.messages'` |

## remailers.mail

```python
from remailers.mail import (
    send_email, send_tor_email,
    build_message,
    SocksSMTP, TorSMTP
)
```

### send_email

```python
send_email(user, pswd, destinatary, subject, contents,
           host="mail.smtp2go.com", port=465, ssl=True)
```

Send email via standard SMTP (non-anonymous).

### send_tor_email

```python
send_tor_email(user, pswd, destinatary, subject, contents,
               host="mail.smtp2go.com", port=465)
```

Send email via Tor SOCKS5 proxy (default 127.0.0.1:9050).

### build_message

```python
build_message(sent_from, to, subject, body) -> str
```

Assemble an RFC-822 email. Parameters:
- `sent_from` (str): From header
- `to` (list[str]): To addresses
- `subject` (str): Subject
- `body` (str): Message body

Returns: RFC-822 formatted string with `\r\n` line endings.

### SocksSMTP

SMTP subclass with SOCKS5 proxy support:

```python
from remailers.mail import SocksSMTP
import socks

smtp = SocksSMTP(
    host="mail.example.com",
    port=25,
    proxy_type=socks.SOCKS5,
    proxy_addr="127.0.0.1",
    proxy_port=9050
)
smtp.login(user, password)
# ... use like standard SMTP
```

### TorSMTP

SMTP_SSL subclass preconfigured for Tor:

```python
from remailers.mail import TorSMTP

with TorSMTP(host="mail.example.com", port=465, tor_port=9050) as server:
    server.login(user, password)
    server.sendmail(from_addr, [to_addr], message)
```

## remailers.keys

```python
from remailers.keys import (
    create_private_key, export_private_key, read_key, encrypt_text
)
```

### create_private_key

```python
create_private_key(name="MyRemailerKey", email=None, expires=None) -> pgpy.PGPKey
```

Generate a new RSA-4096 key.

### export_private_key

```python
export_private_key(path, key=None, binary=False)
```

Save key to file (ASCII or binary).

### read_key

```python
read_key(key_blob) -> pgpy.PGPKey
```

Load key from bytes/string (ASCII or binary).

### encrypt_text

```python
encrypt_text(key, text, creds=None) -> str
```

Encrypt text to a public key (optionally sign with credentials).

## remailers.utils

```python
from remailers.utils import generate_iv

iv = generate_iv(length=8) -> bytes
```

Generate a cryptographically random initialization vector (calls `os.urandom`).

## remailers.zax

```python
from remailers.zax import ZAX, IsNotMyName, MixNym, Thinhose
```

### ZAX base class

```python
class ZAX:
    homepage: str
    domain: str
    key_url: str
    
    def __init__(self, credentials=None, alias="PythonicAnon")
    def register_by_email(self, email, password, headers=None)
    def remail_by_email(self, email, password, destinatary, subject="", body="", headers=None)
    def get_key_by_email(self, email, password)
    def get_nym_pubkey(self) -> str
```

### Built-in servers

- `IsNotMyName` - domain: `is-not-my.name`
- `MixNym` - domain: `mixnym.net`
- `Thinhose` - domain: `nym.thinhose.net`

## Version

```python
from remailers import __version__
```

Current package version (string).

---
[← Security](security.md) · [Home](index.md) · [Remailer Networks →](remailer-networks.md)
