# Security Model

## Cryptography

### Message body (PGP)

Message bodies are protected by PGP (RFC 4880):
- **Algorithm:** RSA-4096 for key exchange
- **Cipher:** AES-256 (primary), Camellia-256
- **Hash:** SHA-512, SHA-256
- **Compression:** BZ2, ZIP, Uncompressed

PGP is a standard, well-audited encryption scheme. Only the holder of the private key can decrypt.

```python
from remailers import Credentials

creds = Credentials("key.asc")
ciphertext = creds.encrypt("message")  # RSA-4096 + AES-256
plaintext = creds.decrypt(ciphertext)
```

### Subject hiding (hSub)

Subjects are hidden with SHA-256 and a random IV:

```
hSub = hex(IV[64 bits] + SHA256(IV || subject)[128 bits])
```

- **One-way:** observers cannot recover the subject
- **Deterministic (for a given IV):** recipient knowing the plaintext can match it
- **Random IV:** same subject encrypted twice gives different hSubs

```python
from remailers import create_hsub, match_hsub

hsub1 = create_hsub("meeting")
hsub2 = create_hsub("meeting")

# Different because IV is random
assert hsub1 != hsub2

# But both match the plaintext
assert match_hsub(hsub1, "meeting")
assert match_hsub(hsub2, "meeting")
```

### Subject hiding (eSub, legacy)

eSub uses Blowfish-CFB with MD5 for Type-I remailer compatibility:

```
eSub = hex(IV[64 bits] + Blowfish_CFB(MD5(key), IV, MD5(subject))[:128 bits])
```

- **Symmetric:** both parties derive the same eSub (allowing proof-of-possession)
- **Weak:** Blowfish and MD5 are outdated
- **Used for:** legacy interop only

eSub does not provide anonymity to eavesdroppers without the shared key. Do not use for new applications.

## IV Entropy

All IVs are generated with `os.urandom()`:

```python
from remailers.utils import generate_iv

iv = generate_iv(8)  # 8 random bytes, cryptographically secure
```

Entropy is OS-dependent:
- Linux: `/dev/urandom` (hardware RNG + entropy pool)
- Windows: CryptGenRandom (Windows Crypto API)
- macOS: `/dev/urandom`

## What the subject scheme does NOT protect

**Subject eSub/hSub provides hiding from passive observers, not from the SMTP/NNTP server itself:**

- The server sees the plaintext subject in the NNTP/SMTP protocol
- Server admins can read your subjects if they inspect logs
- Subject timing (when messages are posted/sent) is visible
- Message size and frequency are visible

To protect against server admins, encrypt the entire article via PGP or use Tor to hide IP.

## What the message body encryption DOES protect

PGP encryption of the message body protects from:
- Passive eavesdropping on the network
- Server-side eavesdropping (server sees only ciphertext)
- Interception in transit
- Unauthorized third parties

The server cannot read the plaintext message without your private key.

## Threat model

### Adversary 1: Passive network observer

Protected by:
- NNTP/SMTP over TLS (encrypted in transit)
- PGP encryption (message body unreadable)
- hSub (subject hidden one-way)

### Adversary 2: Server admin or ISP

Protected by:
- PGP encryption (message body unreadable)

Not protected by:
- Subject hiding (server sees plaintext subject)
- Use Tor or a proxy to hide IP

### Adversary 3: Recipient's server admin

Protected by:
- Encryption to recipient's key (only they can decrypt)

Not protected by:
- Subject hiding (their mail server sees plaintext)

### Adversary 4: Government/law enforcement

Protected by:
- Strong cryptography (practical key recovery infeasible)

Not protected by:
- Timing analysis (when you send messages)
- Behavioral analysis (your posting patterns)
- Metadata (who you're communicating with, via subject matching)

## Best practices

1. **Always use PGP encryption** - do not post plaintext to `alt.anonymous.messages`
2. **Use hSub for new code** - eSub is legacy only
3. **Encrypt subjects too** (if needed) - use PGP encryption or eSub as an extra layer
4. **Use Tor** - for IP anonymity and defense against ISP/server-side analysis
5. **Use Tor email** - for anonymous SMTP gateways (remailers.mail.send_tor_email)
6. **Rotate keys periodically** - reduce exposure if a key is compromised
7. **Don't reuse subjects across identities** - correlation attacks
8. **Use strong passphrases** - on your PGP key file

## Known limitations

- **Type-I remailer network (eSub) is largely defunct** - most servers are offline
- **hSub/eSub do not encrypt the subject to the recipient** - they only hide it from observers. The NNTP server still sees plaintext
- **Message timing is visible** - an adversary can see when you post (use artificial delays if needed)
- **No forward secrecy** - compromised private key reveals all past messages

## Cryptanalysis

- **PGP (RSA-4096 + AES-256):** NIST-approved, no practical breaks known
- **SHA-256 (hSub):** collision-resistant, no practical breaks known
- **Blowfish (eSub):** small block size (64 bits), problematic for large messages. Deprecated by Schneier in favor of Twofish
- **MD5:** cryptographically broken for collision resistance, but OK for MAC in MD5(subject) (not a cryptographic use)

## Recommended reading

- [RFC 4880](https://tools.ietf.org/html/rfc4880): OpenPGP Message Format
- [RFC 1402](https://tools.ietf.org/html/rfc1402): alt.anonymous.messages charter
- [Schneier, B. (2015).](https://www.schneier.com/cryptography/blowfish/): Blowfish deprecation notes

---
[← ZAX Nym Servers](zax-nyms.md) · [Home](index.md) · [API Reference →](api-reference.md)
