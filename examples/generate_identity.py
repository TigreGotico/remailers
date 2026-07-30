"""Generate or load a PGP identity for anonymous messaging."""
from remailers import Credentials

# Generate a new key and save it (or load if it already exists)
creds = Credentials(
    "anon_identity.asc",
    name="PythonicGhost",
    email="ghost@example.org"
)

print("=== Identity Generated ===\n")
print(f"UID: {creds.private_key.userids[0].name if creds.private_key.userids else 'N/A'}")
print(f"Algorithm: RSA-4096")
print(f"\nPublic key (share this with others):\n")
print(creds.pubkey)
