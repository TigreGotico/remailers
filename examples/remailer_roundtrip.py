"""End-to-end remailer flow against a live server.

  1. generate a PGP identity
  2. derive a hashed subject (hSub) for a code word
  3. encrypt a message to ourselves
  4. verify the local decrypt round-trip
  5. attempt to post it to alt.anonymous.messages
  6. scan the live group and try to decrypt what's there

Reading is anonymous. Posting needs a server that accepts anonymous posts (most
public servers require a free account and answer 441 otherwise).
"""
import os
import tempfile

from remailers import AnonBox, Credentials, create_hsub, match_hsub
from usenet import UsenetServer

SERVER = "paganini.bofh.team"   # accepts anonymous posts, carries the group
GROUP = "alt.anonymous.messages"

# 1. identity ---------------------------------------------------------------
key_path = os.path.join(tempfile.mkdtemp(), "ghost.asc")
creds = Credentials(key_path, name="PythonicGhost")
print("1. generated identity; pubkey starts:",
      creds.pubkey.splitlines()[0])

# 2. hashed subject ---------------------------------------------------------
code_word = f"evil dolphin {os.urandom(2).hex()}"
hsub = create_hsub(code_word)
print(f"2. hSub for {code_word!r}: {hsub}")
assert match_hsub(hsub, code_word), "hSub must match its own subject"

# 3. encrypt ----------------------------------------------------------------
plaintext = "meet at the old mill at 3 PM"
ciphertext = creds.encrypt(plaintext)
print("3. encrypted message:", "BEGIN PGP MESSAGE" in ciphertext)

# 4. local round-trip -------------------------------------------------------
assert creds.decrypt(ciphertext) == plaintext
print("4. local decrypt round-trip: OK")

# 5. post -------------------------------------------------------------------
try:
    with UsenetServer(SERVER, timeout=20) as server:
        resp = server.post(ciphertext, hsub, GROUP)
    print("5. posted:", resp)
except Exception as e:
    print(f"5. post rejected ({type(e).__name__}): {e}")

# 6. scan live traffic ------------------------------------------------------
inbox = AnonBox(creds, UsenetServer(SERVER, timeout=20))
with UsenetServer(SERVER, timeout=20) as s:
    recent = s.get_articles(GROUP, limit=25)
    pgp = [a for a in recent if "BEGIN PGP MESSAGE" in a.text]
    print(f"6. scanned {len(recent)} recent messages, "
          f"{len(pgp)} are PGP-encrypted")
ours = inbox.retrieve(limit=25)
print(f"   {len(ours)} decrypted to our key "
      f"(our own just-posted message, if it landed in the latest batch)")
