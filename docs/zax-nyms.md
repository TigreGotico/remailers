# ZAX Nym Servers (Experimental/Historical)

Nym servers allow anonymous email addresses without a real SMTP account. The ZAX base class and subclasses provide a client interface.

> **Status:** These servers are largely offline or unreliable. This documentation is for historical/research purposes. Do not rely on nym servers for secure anonymous communication.

## Overview

A "nym" is an anonymous pseudonym with a permanent email address. You send mail to the nym server's `send@domain`, and it remail's to the real recipient without revealing your SMTP account.

The `remailers.zax` module provides client support for nym servers.

## ZAX base class

```python
from remailers.zax import ZAX
from remailers import Credentials

class MyNym(ZAX):
    homepage = "https://example.org/nym"
    domain = "nym.example.org"
    key_url = "http://example.org/key.asc"

# Initialize with a Credentials object
creds = Credentials("mynym.asc", name="AnonUser", email="anon@nym.example.org")
nym = MyNym(credentials=creds, alias="AnonUser")

# Your public key is automatically fetched
print(nym.credentials.pubkey)
```

### Attributes

| Attribute | Type | Description |
| --- | --- | --- |
| `homepage` | str | Web URL of the nym server |
| `domain` | str | Email domain (e.g., `nym.example.org`) |
| `key_url` | str | HTTP/HTTPS URL to the nym server's public key |

### Methods

| Method | Signature | Purpose |
| --- | --- | --- |
| `register_by_email(email, password, headers=None)` | register new nym | Create a new nym account via email |
| `remail_by_email(email, password, destinatary, subject, body, headers=None)` | send message | Send an anonymous message through the nym |
| `get_key_by_email(email, password)` | fetch public key | Retrieve the nym server's public key |
| `get_nym_pubkey()` | classmethod | Cached nym server public key |

## Built-in nym servers

Three historical nym servers are defined:

### IsNotMyName

```python
from remailers.zax import IsNotMyName

creds = Credentials("isnotmyname.asc", name="Ghost", email="ghost@is-not-my.name")
nym = IsNotMyName(credentials=creds, alias="Ghost")
```

- Homepage: https://remailer.paranoici.org/nym.php
- Domain: `is-not-my.name`
- Key URL: http://is-not-my.name/key.asc

### MixNym

```python
from remailers.zax import MixNym

creds = Credentials("mixnym.asc", name="Shadow", email="shadow@mixnym.net")
nym = MixNym(credentials=creds, alias="Shadow")
```

- Homepage: https://remailer.paranoici.org/nym.php
- Domain: `mixnym.net`
- Key URL: http://remailer.paranoici.org/nymphet.asc

### Thinhose

```python
from remailers.zax import Thinhose

creds = Credentials("thinhose.asc", name="Echo", email="echo@nym.thinhose.net")
nym = Thinhose(credentials=creds, alias="Echo")
```

- Homepage: nym.thinhose.net
- Domain: `nym.thinhose.net`
- Key URL: https://thinhose.net/key.asc

## Workflow

### 1. Create a Credentials object

```python
from remailers import Credentials

creds = Credentials("mynym.asc", name="PythonicGhost", email="ghost@is-not-my.name")
```

### 2. Register with the nym server

```python
from remailers.zax import IsNotMyName

nym = IsNotMyName(credentials=creds, alias="PythonicGhost")

# Register a new nym account via an email address
nym.register_by_email(
    email="your-real-email@gmail.com",
    password="gmail-app-password"
)
```

The nym server sends you confirmation instructions.

### 3. Send a message through the nym

```python
# Send an anonymous message to someone
nym.remail_by_email(
    email="your-real-email@gmail.com",
    password="gmail-app-password",
    destinatary="recipient@example.org",
    subject="Anonymous message",
    body="Message content"
)
```

The message is remail'd from your nym address (e.g., `ghost@is-not-my.name`) to the recipient.

## Configuration emails

Nym servers use configuration emails for setup. The ZAX client builds these:

```python
# Send raw config to the nym server
nym.register_by_email(
    email="your-email@gmail.com",
    password="password",
    headers={
        "Remailer-Version": "0.4",  # optional config headers
    }
)
```

The config is encrypted to the nym server's public key.

## Message encryption

By default, messages are encrypted and signed:

```python
# This happens automatically:
# 1. Plaintext is encrypted to nym server's pubkey
# 2. Message is signed with your Credentials key
# 3. Encrypted blob is sent via email to the nym's send@ address

nym.remail_by_email(
    email="...",
    password="...",
    destinatary="recipient@example.org",
    subject="Message",
    body="Content"
)
```

## Caching

The nym server's public key is fetched once and cached:

```python
key = nym.get_nym_pubkey()  # fetched via HTTP only once per class
```

To force a refresh:

```python
# Clear the cache (on class level)
IsNotMyName._pubkey = None
```

## Historical notes

Type-I remailers (MixMaster/Nymserver protocol) are mostly defunct. These servers are provided for:
- Research and education
- Testing interop with legacy systems
- Archive purposes

They should not be relied upon for actual anonymous communication. The modern alternative is email encryption (PGP) + Tor SMTP.

## Limitation

The ZAX implementation does not validate responses from the nym server. Error handling is minimal. This is intentional to keep the code simple and suitable for historical/experimental use.
