# Tor Email Delivery

Send anonymous email through a Tor SOCKS proxy.

## Overview

`remailers.mail` provides SMTP/TLS over a SOCKS5 proxy, commonly used to tunnel email through Tor for anonymity.

## Requirements

- A running Tor daemon with SOCKS5 listening on localhost (default `127.0.0.1:9050`)
- An SMTP server that accepts relay (many free services available)
- PGP encryption is applied separately (remailers provides PGP, not automatic email encryption)

## Setup

Start a Tor daemon locally:

```bash
# Linux / macOS
tor

# Or as a service
sudo systemctl start tor

# Check it's running
curl --socks5 127.0.0.1:9050 https://check.torproject.org
```

## send_tor_email

Send a message through Tor:

```python
from remailers.mail import send_tor_email

send_tor_email(
    user="anon@mail.smtp2go.com",
    pswd="app-password",
    destinatary="recipient@example.org",
    subject="Anonymous message",
    contents="Message body"
)
```

Parameters:
- `user` - SMTP sender address (must match your SMTP account)
- `pswd` - SMTP password or app-specific password
- `destinatary` - recipient email address
- `subject` - email subject
- `contents` - email body
- `host` - SMTP server (default `mail.smtp2go.com`)
- `port` - SMTP port (default 465 for TLS)
- `tor_port` - Tor SOCKS port (default 9050)

## TorSMTP class

The underlying `TorSMTP` class extends `SMTP_SSL` with Tor tunneling:

```python
from remailers.mail import TorSMTP

with TorSMTP(host="mail.smtp2go.com", port=465, tor_port=9050) as server:
    server.login(user, password)
    server.sendmail(sender, [recipient], message_text)
```

## SocksSMTP class

Lower-level SOCKS5 SMTP support:

```python
from remailers.mail import SocksSMTP
import socks

smtp = SocksSMTP(
    host="mail.smtp2go.com",
    port=465,
    proxy_type=socks.SOCKS5,
    proxy_addr="127.0.0.1",
    proxy_port=9050
)
smtp.login(user, password)
# ... send messages
smtp.quit()
```

## build_message helper

Construct an RFC-822 email manually:

```python
from remailers.mail import build_message

message = build_message(
    sent_from="anon@mail.smtp2go.com",
    to=["recipient@example.org"],
    subject="Subject",
    body="Message body"
)
print(message)
```

Returns an RFC-822 formatted string (with `\r\n` line endings).

## send_email (non-Tor)

For regular (non-anonymous) SMTP:

```python
from remailers.mail import send_email

send_email(
    user="sender@example.org",
    pswd="password",
    destinatary="recipient@example.org",
    subject="Subject",
    contents="Body",
    host="smtp.gmail.com",
    port=465,
    ssl=True
)
```

## SMTP services that work well

Services accepting anonymous/temporary accounts via Tor:
- `mail.smtp2go.com` - requires account signup, free tier available
- `mx.protonmail.com` - ProtonMail's relay (requires ProtonMail account)
- Self-hosted mail servers (if you control one)

> Note: Many free services are blocked or rate-limited for Tor. SMTP2GO is reliable for low-volume anonymous mail.

## PGP + Tor email

Combine PGP encryption with Tor email for full anonymity:

```python
from remailers import Credentials
from remailers.mail import send_tor_email

# Generate a throwaway PGP key
creds = Credentials("anon.asc", name="Whisper")
recipient_pubkey = """..."""  # recipient's public key

# Encrypt the message
plaintext = "Secret message"
ciphertext = creds.encrypt(plaintext, key=recipient_pubkey)

# Send via Tor
send_tor_email(
    user="anon@mail.smtp2go.com",
    pswd="app-password",
    destinatary="recipient@example.org",
    subject="Encrypted message",
    contents=ciphertext
)
```

The recipient decrypts with their private key locally.

## Error handling

Common errors:

| Error | Reason | Fix |
| --- | --- | --- |
| `Connection refused` on 127.0.0.1:9050 | Tor not running | Start Tor daemon |
| `Authentication failed` | Bad SMTP credentials | Verify username/password |
| `SMTPServerDisconnected` | Server rejected SMTP over Tor | Try a different SMTP service |
| `Temporary failure in name resolution` | Tor SOCKS lookup failed | Ensure `tor_port=9050` matches your Tor config |

## Tor configuration

By default, Tor listens on `127.0.0.1:9050`. To change:

Edit `~/.config/tor/torrc` (or `/etc/tor/torrc`):

```
SocksPort 127.0.0.1:9050
```

Then restart Tor:

```bash
sudo systemctl restart tor
# or
pkill -9 tor && tor
```

## Privacy notes

- Email headers (From, To, Subject if not encrypted) are visible to the SMTP server
- PGP-encrypt the subject and body separately if needed
- Tor prevents IP-based tracking. Timing-based analysis is still possible
- The SMTP server logs your plaintext message. Use end-to-end encryption

---
[← AnonBox](anonbox.md) · [Home](index.md) · [ZAX Nym Servers →](zax-nyms.md)
