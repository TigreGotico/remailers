# Algorithms and Message Formats

This document describes the concrete algorithms and message formats used in the remailer network, with worked examples.

> **Key types on the live network.** Real remailers publish DSA primary keys
> with ElGamal encryption subkeys. PGPy cannot encrypt to ElGamal, so the
> per-layer encryption below is done with the GnuPG backend
> (`remailers.gpg.GPGKeyring.encrypt`, passed to `build_chain` as `encrypt=`).
> The `::`/onion structure is identical regardless of backend. See
> [using-the-network](using-the-network.md).

## Type-I Cypherpunk Message Format

A Type-I message is a nested PGP-encrypted structure. The plaintext of each layer is a `::` block (a pasting token) containing routing headers.

### The `::` Block Format

```
::
Header-Name: Header-Value
Another-Header: Another-Value

<optional body>
```

The block starts with `::`, followed by lines of `Header: Value` pairs, a blank line, and then an optional body. This format allows mail clients to distinguish remailer instructions from the actual message.

The most common headers are:

| Header | Value | Meaning |
|--------|-------|---------|
| `Anon-To` | `email@example.com` | Forward to this email address |
| `Anon-Post-To` | `alt.anonymous.messages` | Post to this newsgroup |
| `Latent-Time` | `2 hours` | Delay before forwarding |
| `Encrypted` | `PGP` | This block is PGP-encrypted |

### Building a Single-Hop Message

For a single remailer, the plaintext is:

```
::
Anon-To: bob@example.com

Hello Bob, this is from Alice.
```

Encrypted to the remailer's key, it becomes:

```
-----BEGIN PGP MESSAGE-----
Version: GnuPG v1.0.0 (GNU/Linux)

jA0ECQMCL7...
...
-----END PGP MESSAGE-----
```

The remailer decrypts this, reads `Anon-To: bob@example.com`, and delivers the body to Bob.

### Building a Multi-Hop Chain

For multiple hops, messages are nested. Each layer is encrypted to the corresponding remailer's key.

**Library API:**

```python
from remailers.cypherpunk import final_request, wrap_encrypted, build_chain

# Step 1: Create the innermost block (what the exit remailer processes)
inner = final_request(dest="bob@example.com", body="Hello Bob")
# This produces:
# ::
# Anon-To: bob@example.com
#
# Hello Bob

# Step 2: Wrap it for the exit remailer (frell)
# (Assuming frell_key is the remailer's PGP public key)
wrapped_for_frell = wrap_encrypted(frell_key, inner)
# This produces:
# ::
# Encrypted: PGP
#
# -----BEGIN PGP MESSAGE-----
# ...
# -----END PGP MESSAGE-----

# Step 3: Wrap it for the entry remailer (dizum)
wrapped_for_dizum = wrap_encrypted(dizum_key, wrapped_for_frell)
# This produces:
# ::
# Encrypted: PGP
#
# -----BEGIN PGP MESSAGE-----
# [encrypted: Anon-To: godot@remailer.frell.eu.org, with wrapped_for_frell as body]
# -----END PGP MESSAGE-----

# Or, use build_chain to do all this automatically:
message, entry_addr = build_chain(
    hops=[(dizum_address, dizum_key), (frell_address, frell_key)],
    dest="bob@example.com",
    body="Hello Bob"
)
# message = the final nested structure
# entry_addr = "remailer@dizum.com" (where to send it)
```

### Worked Example: 2-Hop Chain

Suppose we have:

- **Sender:** Alice
- **Entry remailer:** dizum (`remailer@dizum.com`)
- **Exit remailer:** frell (`godot@remailer.frell.eu.org`)
- **Final recipient:** Bob (`bob@example.com`)
- **Message:** "Hello Bob"

**Step 1:** Build the final block (what frell sees):

```
::
Anon-To: bob@example.com

Hello Bob
```

**Step 2:** Encrypt to frell's key:

```
::
Encrypted: PGP

-----BEGIN PGP MESSAGE-----
Version: GnuPG v1.0.0 (GNU/Linux)

jA0ECQMCxyz...  [encrypted Step 1]
...
-----END PGP MESSAGE-----
```

Call this `payload_frell`.

**Step 3:** Build the block that dizum sees:

```
::
Anon-To: godot@remailer.frell.eu.org

<payload_frell>
```

**Step 4:** Encrypt to dizum's key:

```
::
Encrypted: PGP

-----BEGIN PGP MESSAGE-----
Version: GnuPG v1.0.0 (GNU/Linux)

jA0ECQMCabc...  [encrypted Step 3]
...
-----END PGP MESSAGE-----
```

Call this `final_message`.

**Step 5:** Alice sends `final_message` to `remailer@dizum.com` (via SMTP, optionally over Tor).

**Processing:**

1. **Dizum receives** `final_message`
2. **Dizum decrypts** (using its private key) → sees Step 3:
   ```
   ::
   Anon-To: godot@remailer.frell.eu.org
   
   <payload_frell>
   ```
3. **Dizum extracts** the `Anon-To:` header and forwards `payload_frell` to frell
4. **Frell receives** `payload_frell`
5. **Frell decrypts** (using its private key) → sees Step 1:
   ```
   ::
   Anon-To: bob@example.com
   
   Hello Bob
   ```
6. **Frell delivers** "Hello Bob" to bob@example.com (with `From: noreply@frell` or similar)

**Key property:** 

- Dizum cannot read the inner message (it's encrypted to frell)
- Frell cannot see the sender (no `From:` in Alice's original message)
- Bob cannot reply to Alice (no `Return-Path`)
- An observer between Alice and dizum cannot read the message (it's encrypted end-to-end with PGP to Alice's recipients)

## Hashed Subjects (hSub)

Subjects are metadata that transit plaintext through the remailer network. To hide them, the library provides **hSub** — a deterministic hash of the subject with a random IV.

### Algorithm

```
hSub = hex(IV[64 bits] + SHA256(IV || subject))
```

The first 64 bits (16 hex digits) are a random IV. The remaining bits are the SHA-256 hash of the IV concatenated with the subject (both in bytes).

### Implementation

```python
from hashlib import sha256
from remailers.utils import generate_iv

def create_hsub(text, iv=None, hsublen=48):
    if iv is None:
        iv = generate_iv()  # 8 random bytes
    hashed = sha256(iv + text.encode("utf-8")).digest()
    hsub = iv + hashed
    return hsub.hex()[:hsublen]

def match_hsub(hsub, subject):
    if len(hsub) < 48 or len(hsub) > 80:
        return False
    iv = bytes.fromhex(hsub[:16])  # Extract the IV
    return create_hsub(subject, iv, len(hsub)) == hsub
```

### Properties

- **One-way:** An observer cannot recover the subject from the hSub
- **Deterministic (for a given IV):** The same subject + IV always produces the same hSub
- **Random IV:** Different calls to `create_hsub` produce different hSubs for the same subject
- **Recipient-verifiable:** The recipient, knowing the plaintext subject, can compute the hSub and check if it matches

### Example

```python
from remailers import create_hsub, match_hsub

subject = "meeting at midnight"
hsub = create_hsub(subject)
print(hsub)  # e.g., "a1b2c3d4e5f6...g7h8i9j0" (48+ hex digits)

# Recipient knows the plaintext
assert match_hsub(hsub, "meeting at midnight")

# But an observer cannot recover the subject from hsub alone
assert not ("meeting at midnight" in hsub)

# Different calls produce different hSubs
hsub2 = create_hsub(subject)
assert hsub != hsub2
assert match_hsub(hsub2, "meeting at midnight")
```

### Usage in Remailers

When posting to `alt.anonymous.messages`, you provide the NNTP subject as the hSub:

```python
from usenet import UsenetServer
from remailers import create_hsub, Credentials

creds = Credentials("my_key.asc")
hsub = create_hsub("code word")
plaintext_message = "secret data"
ciphertext = creds.encrypt(plaintext_message)

with UsenetServer("paganini.bofh.team") as server:
    # Subject line will be the hSub; observers cannot recover "code word"
    server.post(ciphertext, hsub, "alt.anonymous.messages")

# Later, recipient knows the plaintext "code word" and can search:
from remailers import AnonBox
inbox = AnonBox(creds, UsenetServer("paganini.bofh.team"))
articles = inbox.retrieve_by_subject("code word")  # Matches hSub automatically
```

## Encrypted Subjects (eSub)

**eSub is legacy and deprecated.** It exists only for compatibility with old Type-I remailers that still use it. New code should use hSub instead.

### Algorithm

```
eSub = hex(IV[64 bits] + Blowfish_CFB(MD5(key), IV, MD5(subject))[:128 bits])
```

Both the sender and recipient must share the same key. The IV is random.

### Implementation

```python
from Crypto.Cipher import Blowfish
from hashlib import md5
from remailers.utils import generate_iv

def create_esub(text, key, iv=None):
    texthash = md5(text.encode("utf-8")).digest()
    keyhash = md5(key.encode("utf-8")).digest()
    if iv is None:
        iv = generate_iv(8)
    crypt1 = Blowfish.new(keyhash, Blowfish.MODE_OFB, iv).encrypt(texthash)[:8]
    crypt2 = Blowfish.new(keyhash, Blowfish.MODE_OFB, crypt1).encrypt(texthash[8:])
    return (iv + crypt1 + crypt2).hex()

def match_esub(text, key, esub):
    if len(esub) != 48:
        return False
    iv = bytes.fromhex(esub[:16])
    return create_esub(text, key, iv) == esub
```

### Properties

- **Symmetric:** Both sender and recipient compute the same eSub if they share the key
- **Deterministic:** The same (text, key, IV) always produces the same eSub
- **Weak crypto:** Blowfish and MD5 are outdated; MD5 is broken for collision resistance
- **Usage:** Legacy alt.anonymous.messages eSub-based filtering

### Example

```python
from remailers import create_esub, match_esub

key = "shared_secret"
subject = "meeting"
esub = create_esub(subject, key)

# Recipient with the same key can match
assert match_esub(subject, key, esub)

# Without the key, the recipient cannot compute this
assert not match_esub(subject, "wrong_key", esub)
```

## Type-II Mixmaster Packets

The library does not build Type-II Mixmaster packets. It only builds Type-I messages. Type-II remailers can accept Type-I messages, since they recognize the `::` block format, so no changes are needed to interoperate.

**Type-II packet structure (for reference):**

- All packets are a fixed size (about 20 KB) to defeat traffic analysis
- Packets contain an encrypted chain of RSA-encrypted "hop" information
- Each hop is encrypted to the next remailer's key and contains routing info and a secret to decrypt the next hop
- Messages are pooled (held in a queue) and randomly reordered before forwarding
- This defeats correlation attacks and provides stronger anonymity than Type-I

Mixmaster is deployed in the live network (remailers supporting the `mix` flag), but the library's `remailers.cypherpunk` module targets Type-I only, which is simpler and sufficient for most use cases.

## Summary Table

| Feature | Type-I (Cypherpunk) | Type-II (Mixmaster) | hSub | eSub |
|---------|-------------------|-------------------|------|------|
| **Format** | `::` pasting token | Binary packet | SHA-256 hash | Blowfish CFB |
| **Size** | Variable | Fixed (~20 KB) | 48-80 hex digits | 48 hex digits |
| **Pooling** | Optional (if remailer supports `latent`) | Built-in | N/A | N/A |
| **Crypto** | PGP (RSA-4096 + AES-256) | RSA-4096 | SHA-256 | MD5 + Blowfish |
| **One-way** | No (plaintext in `Anon-To:`) | No (RSA-encrypted hops visible) | Yes (SHA-256) | No (symmetric) |
| **Modern** | Yes, still in use | Yes, in use (via Yamn) | Yes (recommended) | No (legacy only) |
| **Library support** | Yes (`remailers.cypherpunk`) | No (Type-I sufficient) | Yes (`remailers.hsub`) | Yes (`remailers.esub`) |

---
[← Architecture](architecture.md) · [Home](index.md) · [Privacy Guarantees →](privacy-guarantees.md)
