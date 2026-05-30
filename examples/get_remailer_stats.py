"""Read the live remailer stats from Usenet and print the network."""
from remailers.network import fetch_live_remailers

remailers = fetch_live_remailers()
print(f"{len(remailers)} active remailers:\n")
for r in sorted(remailers, key=lambda x: x.uptime, reverse=True):
    flags = " ".join(sorted(c for c in ("cpunk", "mix", "pgp", "post", "hsub")
                            if r.supports(c)))
    print(f"  {r.name:10} {r.address:32} up={r.uptime:7} lat={r.latency:6} [{flags}]")
