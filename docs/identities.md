# Managing Identities (PGP Keys)

## Credentials class

`Credentials` manages a PGP secret key for encryption, decryption, and signing:

```python
from remailers import Credentials

# Loads existing key or generates a new one
creds = Credentials(
    path="my_key.asc",      # file path for the key
    name="PythonicAnon",    # UID name (only used if generating new key)
    email="anon@example.org",  # email (optional, only if new key)
    expires=None            # expiry (timedelta or datetime, optional)
)
```

If the file exists, it is loaded. If not, a new key is generated and saved.

### File formats

Credentials auto-detects format based on file extension:
- `.asc`, `.txt` — ASCII-armored (default for text)
- Other extensions — binary format

```python
# ASCII-armored (human-readable)
creds = Credentials("key.asc")

# Binary format
creds = Credentials("key.bin")
```

## Key generation

Create a new key directly:

```python
from remailers.keys import create_private_key
from datetime import timedelta

# RSA-4096, with AES-256 cipher and SHA-512 hash
key = create_private_key(
    name="PythonicAnon",
    email="anon@example.org",
    expires=timedelta(days=365)  # or a datetime
)
```

The generated key uses:
- **Algorithm:** RSA-4096
- **Cipher:** AES-256, Camellia-256
- **Hash:** SHA-512, SHA-256
- **Compression:** BZ2, ZIP, Uncompressed

## Key export

Save a key to disk:

```python
from remailers.keys import export_private_key, create_private_key

key = create_private_key(name="MyKey")
export_private_key("my_key.asc", key=key, binary=False)  # ASCII
export_private_key("my_key.bin", key=key, binary=True)   # binary
```

Or use `Credentials` which saves automatically on creation.

## Loading keys

Load a key from bytes or a blob:

```python
from remailers.keys import read_key

with open("my_key.asc") as f:
    key_blob = f.read()

key = read_key(key_blob)
```

`Credentials` uses this internally.

## Using Credentials

Once created, use `Credentials` to encrypt and decrypt:

### Encrypt

```python
creds = Credentials("my_key.asc")

# Encrypt with your own public key
plaintext = "secret message"
ciphertext = creds.encrypt(plaintext)
print(ciphertext)
```

### Decrypt

```python
# Decrypt a message encrypted to you
decrypted = creds.decrypt(ciphertext)
print(decrypted)
```

### Signing

Sign a message for verification:

```python
# Sign a message (optional recipient list)
signed_message = creds.sign(
    plaintext_message,
    intended_recipients=None  # or list of PGP keys
)
```

The `.pubkey` property returns your public key in ASCII-armored format:

```python
print(creds.pubkey)  # for distribution to others
```

## Expiry

Keys can have an expiry date. Use `timedelta` or `datetime`:

```python
from datetime import timedelta

# Expire in 1 year
creds = Credentials(
    "my_key.asc",
    name="TempAnon",
    expires=timedelta(days=365)
)

# Or an exact datetime
from datetime import datetime
creds = Credentials(
    "my_key.asc",
    name="TempAnon",
    expires=datetime(2026, 5, 30)
)
```

## Key material

Access the underlying PGP key:

```python
creds = Credentials("my_key.asc")
key_object = creds.private_key  # pgpy.PGPKey object
```

For advanced use, work directly with pgpy:

```python
import pgpy

key, _ = pgpy.PGPKey.from_blob(open("my_key.asc").read())
message = pgpy.PGPMessage.new("plaintext")
encrypted = key.encrypt(message)
```
