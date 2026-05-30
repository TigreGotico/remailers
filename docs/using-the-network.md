# Using the Remailer Network: Practical Guide

This guide walks through the complete workflow for discovering live remailers, building a message chain, and sending anonymously.

## Step 1: Discover Live Remailers

The `remailers.network` module fetches the current remailer list from Usenet and loads their public keys.

```python
from remailers.network import (
    fetch_live_remailers,
    fetch_keyring_blob,
    load_keyring,
    key_for,
)

# Get the live remailer list from alt.privacy.anon-server.stats
remailers = fetch_live_remailers(server="paganini.bofh.team", limit=12)
print(f"Found {len(remailers)} active remailers:")
for r in remailers:
    print(f"  {r.name}: {r.address} | uptime={r.uptime} | caps={r.capabilities}")

# Fetch the published PGP keyring
keyring_blob = fetch_keyring_blob()  # from echolot.theremailer.net
keyring = load_keyring(keyring_blob)  # {email → PGPKey}
print(f"Loaded {len(keyring)} keys")
```

## Step 2: Select Remailers by Capability

Different use cases require different capability sets. Choose based on your goals:

### Sending Email Anonymously

Minimum requirements:
- **Entry & intermediate hops:** `cpunk` (Type-I Cypherpunk format) + `pgp` (PGP encryption)
- **Exit remailer:** `cpunk` + `pgp` + any downstream capability

**Code:**

```python
from remailers.network import fetch_live_remailers

remailers = fetch_live_remailers()

# Filter to suitable remailers
suitable = [r for r in remailers 
            if r.is_cpunk and r.accepts_pgp]

print(f"Suitable for anonymous email: {len(suitable)}")
for r in suitable:
    print(f"  {r.name} ({r.uptime})")
```

**Preferred choices (as of 2026):**

```
dizum:    remailer@dizum.com        (99% uptime, fully featured)
frell:    godot@remailer.frell.eu.org (95% uptime, reliable)
paranoia: mixmaster@remailer.paranoici.org (98% uptime)
```

### Posting to Usenet (alt.anonymous.messages)

**Exit remailer must have:** `post` (mail-to-news capability)

**Code:**

```python
remailers = fetch_live_remailers()

# Filter for Usenet posting capability
posting_remailers = [r for r in remailers if r.can_post]

print(f"Can post to Usenet: {len(posting_remailers)}")
for r in posting_remailers:
    print(f"  {r.name}")
```

### Using Latency and Pooling

For better traffic-analysis resistance, use remailers with `latent` and `reord` (reordering) flags.

**Code:**

```python
remailers = fetch_live_remailers()

# Filter for latency support (pooling + reordering)
pooling = [r for r in remailers 
           if r.supports("latent") and r.supports("reord")]

print(f"Support latency/pooling: {len(pooling)}")
```

## Step 3: Create a PGP Identity

Generate (or load) your PGP key:

```python
from remailers import Credentials

# Create a new key or load an existing one
creds = Credentials(
    path="my_anon_key.asc",
    name="AnonymousWriter",
    email="anonymouswriter@nowhere.invalid"
)

print("Public key:")
print(creds.pubkey)

# The key is automatically saved to my_anon_key.asc
# Load it later with:
creds = Credentials("my_anon_key.asc")
```

## Step 4: Build a Message Chain

`build_chain` assembles the nested PGP-encrypted onion. Each layer is encrypted
to a remailer's key by an `encrypt(recipient, plaintext)` callable.

> **Real remailer keys are DSA primary + ElGamal encryption subkeys.** PGPy
> cannot encrypt to ElGamal, so to reach the live network you must use the
> **GnuPG backend** (`remailers.gpg.GPGKeyring`), which encrypts by recipient
> address. PGPy's `load_keyring`/`key_for` are still useful for inspecting the
> ring and for any RSA keys, but not for encrypting to the current network.

```python
from remailers.cypherpunk import build_chain
from remailers.gpg import GPGKeyring, gpg_available
from remailers.network import fetch_live_remailers, fetch_keyring_blob

assert gpg_available()
remailers = fetch_live_remailers()

with GPGKeyring(fetch_keyring_blob()) as gpg:
    have = set(gpg.recipients())
    chain = [r for r in remailers
             if r.is_cpunk and r.accepts_pgp and r.address in have][:3]

    # recipient is the ADDRESS (gpg looks it up); encrypt is gpg.encrypt
    message, entry_addr = build_chain(
        hops=[(r.address, r.address) for r in chain],
        dest="alice@example.com",
        body="Hello Alice, this is from a friend.",
        encrypt=gpg.encrypt,
    )

print(f"Message ready to send to: {entry_addr}")
```

When you control the keys (e.g. an RSA test remailer), the default PGPy backend
works: pass `hops=[(address, pgp_key), ...]` and omit `encrypt`.

## Step 5a: Send via Email (SMTP)

Deliver the message to the entry remailer over SMTP:

```python
from remailers.cypherpunk import send_chain

send_chain(
    message=message,
    entry_address=entry_addr,
    user="your_smtp_account@gmail.com",
    password="your_app_password",  # Use an app-specific password
    host="smtp.gmail.com",
    port=587,
    tor=False  # Set to True if running Tor
)
print("Message sent!")
```

**For Gmail:**

1. Enable 2-factor authentication
2. Generate an app-specific password: https://myaccount.google.com/apppasswords
3. Use that password in the `send_chain` call

**For other SMTP servers:**

- Adjust `host` and `port`
- Consider using a temporary email service (e.g., Proton Mail, 10minutemail)

### Send via Tor

If you have Tor running locally (port 9050), set `tor=True`:

```python
send_chain(
    message=message,
    entry_address=entry_addr,
    user="your_smtp@example.com",
    password="password",
    tor=True  # Routes through Tor
)
```

## Step 5b: Post to Usenet (alt.anonymous.messages)

If using a Usenet posting chain, post instead of emailing:

```python
from usenet import UsenetServer
from remailers import create_hsub

# Use hSub instead of plaintext subject
code_word = "secret meeting location"
hsub = create_hsub(code_word)

with UsenetServer("paganini.bofh.team") as server:
    server.post(message, hsub, "alt.anonymous.messages")
    print(f"Posted with hSub: {hsub}")
```

**Note:** Use `Anon-Post-To:` instead of `Anon-To:` in the final block:

```python
message, entry_addr = build_chain(
    hops=[...],
    anon_post_to="alt.anonymous.messages",  # ← Instead of dest=
    body="Anonymous message body"
)
```

## Step 6: Recipient Retrieves and Decrypts

The recipient uses `AnonBox` to retrieve messages and decrypt them:

```python
from remailers import Credentials, AnonBox, match_hsub
from usenet import UsenetServer

# Recipient's credentials (they generated their own key)
creds = Credentials("my_key.asc")

# Connect to a Usenet server
inbox = AnonBox(creds, UsenetServer("paganini.bofh.team"))

# Retrieve all messages decryptable with their key
articles = inbox.retrieve(limit=50)
print(f"Retrieved {len(articles)} messages")
for article in articles:
    print(f"Subject: {article.subject}")
    print(article.body[:200])
```

### Retrieve by hSub Subject

If using hashed subjects, the recipient matches by plaintext:

```python
# Recipient knows the code word
inbox = AnonBox(creds, UsenetServer("paganini.bofh.team"))

articles = inbox.retrieve_by_subject(
    "secret meeting location",
    limit=100,
    hsubs=True  # Match hSub
)
print(f"Found {len(articles)} messages with matching subject")
```

## Complete End-to-End Example

Here's a complete workflow:

```python
# ============================================================================
# SENDER SIDE
# ============================================================================
from remailers import Credentials, create_hsub
from remailers.cypherpunk import build_chain
from remailers.gpg import GPGKeyring
from remailers.network import fetch_live_remailers, fetch_keyring_blob

# 1. Sender creates a PGP identity
sender_creds = Credentials("sender_key.asc", name="AnonymousAlice")

# 2. Discover remailers + open the GnuPG keyring (real keys are ElGamal)
remailers = fetch_live_remailers()
with GPGKeyring(fetch_keyring_blob()) as gpg:
    # 3. Build a chain through PGP-capable remailers
    have = set(gpg.recipients())
    chain = [r for r in remailers if r.is_cpunk and r.accepts_pgp and r.address in have][:3]
    message, entry_addr = build_chain(
        hops=[(r.address, r.address) for r in chain],
        anon_post_to="alt.anonymous.messages",
        body="This is a secret message from Alice.",
        encrypt=gpg.encrypt,
    )

# 4. Send via Usenet
from usenet import UsenetServer
hsub = create_hsub("alice_message_code")
with UsenetServer("paganini.bofh.team") as server:
    server.post(message, hsub, "alt.anonymous.messages")

print(f"Message posted! hSub: {hsub}")

# ============================================================================
# RECIPIENT SIDE (Bob retrieves the message)
# ============================================================================
from remailers import AnonBox

# 1. Bob creates his PGP identity
bob_creds = Credentials("bob_key.asc", name="AnonymousBob")

# 2. Connect to Usenet
inbox = AnonBox(bob_creds, UsenetServer("paganini.bofh.team"))

# 3. Retrieve messages (can try directly or by subject)
all_messages = inbox.retrieve(limit=50)
print(f"Retrieved {len(all_messages)} decryptable messages")

# 4. Or retrieve by the code word (if Bob knows it)
code_messages = inbox.retrieve_by_subject(
    "alice_message_code",
    hsubs=True
)
for article in code_messages:
    print(f"Found message for: {article.subject}")
    print(article.body)
```

## Practical Checklist

Before sending:

- [ ] **Remailers are online** — Check the latest stats (they should be < 1 day old)
- [ ] **Keys are up-to-date** — Fetch the keyring fresh; old keys won't work
- [ ] **Chain is diverse** — Use at least 3 different remailers
- [ ] **Remailers support required capabilities** — Check `cpunk`, `pgp`, `post` as needed
- [ ] **SMTP account works** — Test sending a normal email first
- [ ] **Message encrypts locally** — Test a round-trip before sending live:

```python
# Test: encrypt and decrypt with your own key
plaintext = "test message"
ciphertext = creds.encrypt(plaintext)
recovered = creds.decrypt(ciphertext)
assert recovered == plaintext
```

- [ ] **No metadata leaks** — Check that the message body doesn't contain identifying info
- [ ] **Timing is varied** — Send at different times than other messages, if trying to hide patterns

## Troubleshooting

### Remailers Not Responding

```
usenet.error.NNTPTemporaryError: no response
```

The Usenet server or remailer may be down. Check:

```python
remailers = fetch_live_remailers(limit=20)  # Try more articles
if not remailers:
    print("No active remailers found; network may be down")
```

### Key Not Found

```
KeyError: 'remailer@example.com'
```

The keyring doesn't have a key for that remailer. Check:

```python
keyring = load_keyring(fetch_keyring_blob())
print("Keys in keyring:", list(keyring.keys()))
```

Some remailers may not publish their keys; in that case, you must fetch the key from their website manually.

### PGP Decryption Fails

```
pgpy.errors.PGPError: ...
```

The message is not encrypted to your key, or the encryption is corrupted. Ensure:

- The sender encrypted to your public key
- The message wasn't modified in transit
- Your private key is the correct one

### SMTP Authentication Failed

```
smtplib.SMTPAuthenticationError
```

Check:

- Gmail: Use app-specific password, not your main password
- Other services: Verify credentials and server settings
- Firewall: Check if port 465/587 is open

## Advanced: Custom Headers

You can add extra headers to the routing block:

```python
message, entry_addr = build_chain(
    hops=[...],
    dest="alice@example.com",
    body="message",
    extra_headers={"X-Custom": "value"}
)
```

These are transparent to the remailer (they don't affect routing) but can be used by the recipient.

## Advanced: Latent Time

Add a delay at the exit remailer:

```python
message, entry_addr = build_chain(
    hops=[...],
    dest="alice@example.com",
    body="message",
    latent="2 hours"  # Delay 2 hours before delivering
)
```

The exit remailer will pool the message and forward it after the specified delay, providing some timing-analysis resistance.

## See Also

- [Remailer Networks](remailer-networks.md) — overview of live remailers
- [Architecture](architecture.md) — how chains work internally
- [Algorithms](algorithms.md) — message format details
- [Privacy Guarantees](privacy-guarantees.md) — security assumptions and threat model
- [Security](security.md) — cryptography and IV entropy
- [AnonBox](anonbox.md) — detailed message retrieval
- [Subjects](subjects.md) — hSub and eSub details
