"""Build a real Type-I message addressed to live remailers.

Fetches the live network + published keyring, then assembles a nested Cypherpunk
onion that posts to alt.test through a chain. Real remailer keys are DSA/ElGamal,
so encryption uses the GnuPG backend (PGPy cannot encrypt to ElGamal). It does
NOT send — delivery needs an email sender (see remailers.cypherpunk.send_chain).
"""
from remailers.cypherpunk import build_chain
from remailers.gpg import GPGKeyring, gpg_available
from remailers.network import fetch_keyring_blob, fetch_live_remailers

if not gpg_available():
    raise SystemExit("gpg is required to encrypt to real remailer keys")

remailers = fetch_live_remailers()
blob = fetch_keyring_blob()

with GPGKeyring(blob) as gpg:
    have_key = set(gpg.recipients())
    # PGP-capable Cypherpunk remailers we hold a key for; exit must post
    usable = [r for r in remailers
              if r.is_cpunk and r.accepts_pgp and r.address in have_key]
    chain = [r for r in usable if r.can_post][:2] or usable[:2]
    print("chain:", " -> ".join(f"{r.name}<{r.address}>" for r in chain))

    hops = [(r.address, r.address) for r in chain]   # recipient = address (gpg)
    message, entry = build_chain(hops, anon_post_to="alt.test",
                                 body="usenet/remailers compatibility check, ignore",
                                 encrypt=gpg.encrypt)

print("\nsend this to the entry remailer:", entry)
print("-" * 60)
print(message[:500])
print("... (nested onion; each layer is BEGIN PGP MESSAGE for the next hop)")
