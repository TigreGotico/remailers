"""Offline PGP encryption and decryption with one Credentials object."""
from remailers import Credentials

# Load (or create) a PGP identity
creds = Credentials("test_key.asc", name="TestUser")

# Plaintext message
plaintext = "This is a secret message that only I can decrypt."
print(f"Plaintext:\n{plaintext}\n")

# Encrypt to your own public key
ciphertext = creds.encrypt(plaintext)
print(f"Ciphertext (encrypted to your key):\n{ciphertext[:100]}...\n")

# Decrypt with your private key
decrypted = creds.decrypt(ciphertext)
print(f"Decrypted:\n{decrypted}\n")

# Verify round-trip
assert decrypted == plaintext, "Decryption failed!"
print("✓ Encryption/decryption successful")
