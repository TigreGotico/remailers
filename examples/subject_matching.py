"""Offline demonstration of subject matching: hSub and eSub round-trips."""
from remailers import create_hsub, match_hsub, create_esub, match_esub

print("=== hSub (Hashed Subject) ===\n")

# Create an hSub (one-way hash)
plaintext = "secret meeting code"
hsub = create_hsub(plaintext)
print(f"Subject: '{plaintext}'")
print(f"hSub:    {hsub}")
print()

# Recipient with the plaintext subject can match it
match_result = match_hsub(hsub, plaintext)
print(f"match_hsub(hsub, '{plaintext}'): {match_result}")

# Different subject won't match
wrong_match = match_hsub(hsub, "different code")
print(f"match_hsub(hsub, 'different code'): {wrong_match}")

print("\n" + "="*50)
print("=== eSub (Encrypted Subject, Legacy) ===\n")

# Both parties share a secret key
shared_key = "my-shared-secret"
plaintext = "message code"

# Create an eSub
esub = create_esub(plaintext, key=shared_key)
print(f"Subject: '{plaintext}'")
print(f"Key:     '{shared_key}'")
print(f"eSub:    {esub}")
print()

# Recipient with the key can match it
match_result = match_esub(plaintext, shared_key, esub)
print(f"match_esub('{plaintext}', key, esub): {match_result}")

# Wrong key won't match
wrong_match = match_esub(plaintext, "wrong-key", esub)
print(f"match_esub('{plaintext}', 'wrong-key', esub): {wrong_match}")

print("\n" + "="*50)
print("=== IV Randomness ===\n")

# Each call generates a new IV, so the same subject produces different hSubs
hsub1 = create_hsub("code")
hsub2 = create_hsub("code")
print(f"hSub 1: {hsub1}")
print(f"hSub 2: {hsub2}")
print(f"Same subject, different hSubs: {hsub1 != hsub2}")
print()

# But both match the plaintext
print(f"Both match the plaintext:")
print(f"  match_hsub(hsub1, 'code'): {match_hsub(hsub1, 'code')}")
print(f"  match_hsub(hsub2, 'code'): {match_hsub(hsub2, 'code')}")
