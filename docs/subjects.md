# Hashed and Encrypted Subjects

Usenet article subjects are visible in cleartext to anyone who can read the group. Two schemes hide the subject from observers while allowing intended recipients to identify messages meant for them.

## hSub (Hashed Subject)

**Use hSub for new code.** SHA-256 one-way hashing with a random 8-byte IV.

### Create

```python
from remailers import create_hsub

# One-way hash of the subject
hsub = create_hsub("secret meeting code")
print(hsub)  # 48 hex characters (192 bits: 64-bit IV + 128-bit SHA256 prefix)
```

Structure:
```
hSub = hex(IV[8 bytes] + SHA256(IV + subject)[first 16 bytes])
```

The IV is random per call, so the same subject produces different hSubs:

```python
code = "meeting"
hsub1 = create_hsub(code)
hsub2 = create_hsub(code)
print(hsub1 != hsub2)  # True – different IVs
```

### Match

A recipient knowing the plaintext subject can check if an article is for them:

```python
from remailers import match_hsub

# Check if this hSub matches the known subject
result = match_hsub(hsub, "secret meeting code")
assert result  # True if it matches
```

Only the person who knows the original subject can match it. The hSub leaks no information to observers.

### Length control

By default, hSub is 48 hex characters (192 bits). You can expand it:

```python
# Use more bytes of the hash for extra security
hsub = create_hsub("code", hsublen=64)  # 256 bits
```

Valid range: 48–80 hex characters. The low bound is Type-I eSub compat (192 bits); the high bound is the full SHA256 output plus IV (320 bits).

### IV parameter (advanced)

To create an hSub with a known IV (for testing or deriving), pass it:

```python
from remailers.utils import generate_iv

iv = generate_iv(8)  # 8 random bytes
hsub = create_hsub("subject", iv=iv)
```

## eSub (Encrypted Subject)

**For legacy Type-I remailer interop only.** Blowfish-CFB encryption with MD5.

### Create

```python
from remailers import create_esub

# Shared secret between sender and recipient
shared_key = "my-shared-secret"

# Blowfish-encrypted subject
esub = create_esub("message code", key=shared_key)
print(esub)  # 48 hex characters (192 bits: 64-bit IV + 128-bit ciphertext)
```

Structure:
```
eSub = hex(IV[8 bytes] + Blowfish_CFB(MD5(key), IV, MD5(subject))[:16 bytes])
```

Like hSub, eSub includes a random IV, so repeated encryption gives different results.

### Match

Both parties must know the shared key:

```python
from remailers import match_esub

# Recipient decrypts using the shared key
result = match_esub("message code", shared_key, esub)
assert result  # True
```

### When to use eSub

Only for compatibility with legacy Type-I remailers. Advantages:
- Symmetric (both parties derive the same encryption, so proof-of-possession is possible)
- Compact (48 hex chars)

Disadvantages:
- Shared secret distribution is hard (both parties need to know it beforehand)
- Blowfish is weak by modern standards
- Type-I remailer network is mostly defunct

**New code should use hSub.**

## Comparison

| Property | hSub | eSub |
| --- | --- | --- |
| Algorithm | SHA-256 (one-way) | Blowfish-CFB (symmetric) |
| IV size | 8 bytes (64 bits) | 8 bytes (64 bits) |
| Output size | 48 hex chars (192 bits) | 48 hex chars (192 bits) |
| Security | No leakage to observers | No leakage if key is secret |
| Key distribution | None (recipient knows subject plaintext) | Requires shared secret exchange |
| Use case | New code, public subjects | Legacy Type-I interop |

## Usage in AnonBox

Retrieve messages by subject:

```python
from usenet import UsenetServer
from remailers import Credentials, AnonBox, create_hsub, create_esub

creds = Credentials("anon.asc")
server = UsenetServer("news.example.org")
inbox = AnonBox(creds, server)

# Retrieve by hSub (plaintext subject is known)
inbox.retrieve_by_subject("my message code", hsubs=True, esubs=False)

# Or by eSub (with shared key)
inbox.retrieve_by_subject("code", esub_key="shared-secret", esubs=True, hsubs=False)

# Or match exact subject in cleartext
inbox.retrieve_by_subject("Exact Subject")
```

## IV entropy

Both schemes use `remailers.utils.generate_iv()`, which calls `os.urandom()`:

```python
from remailers.utils import generate_iv

iv = generate_iv(8)  # 8 random bytes, cryptographically secure
```

IV is never reused for the same subject and key; a fresh one is generated per call.
