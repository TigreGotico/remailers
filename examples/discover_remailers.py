"""Recon: is the classic remailer network still alive in 2026?

Reads the remailer stats Usenet group and the canonical web stats / nym key
sources. Run once to see what still responds.
"""
from usenet import UsenetServer

# 1. Usenet: the stats pinger posts here -----------------------------------
STATS_GROUP = "alt.privacy.anon-server.stats"
STATS_SERVER = "paganini.bofh.team"

print(f"== {STATS_GROUP} on {STATS_SERVER} ==")
try:
    with UsenetServer(STATS_SERVER, timeout=20) as s:
        arts = s.get_articles(STATS_GROUP, limit=12)
        print(f"{len(arts)} recent articles")
        for a in arts:
            print(" ", a.date, "|", repr(a.subject)[:70])
        # dump the body of the newest stats post
        for a in arts:
            if "stat" in (a.subject or "").lower() or "remailer" in (a.subject or "").lower():
                print("\n--- newest stats body (first 1500 chars) ---")
                print(a.text[:1500])
                break
except Exception as e:
    print("  error:", type(e).__name__, e)

# 2. Web: stats pages + nym keys -------------------------------------------
URLS = [
    "https://remailer.paranoici.org/",
    "https://remailer.paranoici.org/rlist.php",
    "https://remailer.paranoici.org/mlist.php",
    "https://www.mixmin.net/",
    "https://stats.mixmin.net/",
    "https://www.dizum.com/",
    "http://is-not-my.name/key.asc",
    "http://remailer.paranoici.org/nymphet.asc",
    "https://thinhose.net/key.asc",
    "https://sec3.net/",
]


def _session():
    try:
        from unblock_requests import CloudflareSession
        return CloudflareSession(env_prefix="REMAILERS", wayback_fallback=True)
    except ImportError:
        import requests
        return requests.Session()


print("\n== web stats / nym keys ==")
sess = _session()
for url in URLS:
    try:
        r = sess.get(url, timeout=15)
        body = r.text or ""
        head = body.strip().splitlines()[:1]
        print(f"  {r.status_code}  {url}  ({len(body)}b)  {head[0][:50] if head else ''}")
    except Exception as e:
        print(f"  ERR  {url}  {type(e).__name__}: {str(e)[:50]}")
