"""Discover the live Cypherpunk/Mixmaster remailer network.

The Frelled/echolot pinger publishes remailer stats to the Usenet group
``alt.privacy.anon-server.stats`` (and to the web). Each stats post carries a
``$remailer{...}`` capability block listing every active remailer's address and
features, plus a latency/uptime table. This module reads and parses that, and
fetches the published PGP keyring so messages can be encrypted to real keys.
"""
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from usenet import UsenetServer

STATS_GROUP = "alt.privacy.anon-server.stats"
STATS_SERVER = "paganini.bofh.team"
# echolot publishes the concatenated remailer public keys here
KEYRING_URL = "http://echolot.theremailer.net/sideview/pgp-all.asc"

_CAPS_RE = re.compile(r'\$remailer\{"([^"]+)"\}\s*=\s*"<([^>]+)>\s*([^"]*)"')
# a stats-table row: name, latent-hist, latent, uptime-hist, uptime, options...
_ROW_RE = re.compile(r'^(\w[\w.-]*)\s+\S+\s+(\S+)\s+\S+\s+([\d.]+%)')


@dataclass(frozen=True)
class Remailer:
    """One remailer advertised in the live stats."""

    name: str
    address: str
    capabilities: frozenset = field(default_factory=frozenset)
    latency: str = ""
    uptime: str = ""

    def supports(self, cap: str) -> bool:
        return cap in self.capabilities

    @property
    def email(self) -> str:
        return self.address

    @property
    def is_cpunk(self) -> bool:
        return "cpunk" in self.capabilities

    @property
    def accepts_pgp(self) -> bool:
        return "pgp" in self.capabilities

    @property
    def can_post(self) -> bool:
        return "post" in self.capabilities


def parse_stats(text: str) -> List[Remailer]:
    """Parse a Frelled/echolot stats post into Remailer records."""
    latency: Dict[str, str] = {}
    uptime: Dict[str, str] = {}
    for line in text.splitlines():
        m = _ROW_RE.match(line.strip())
        if m and ":" in m.group(2) or (m and m.group(2).isdigit()):
            name, lat, up = m.group(1), m.group(2), m.group(3)
            latency[name] = lat
            uptime[name] = up

    remailers = []
    for name, address, caps in _CAPS_RE.findall(text):
        remailers.append(Remailer(
            name=name,
            address=address,
            capabilities=frozenset(caps.split()),
            latency=latency.get(name, ""),
            uptime=uptime.get(name, ""),
        ))
    return remailers


def fetch_live_remailers(server: str = STATS_SERVER, limit: int = 12) -> List[Remailer]:
    """Read the newest Cypherpunk stats post from Usenet and parse it."""
    with UsenetServer(server, timeout=20) as nntp:
        for article in nntp.get_articles(STATS_GROUP, limit=limit):
            subject = article.subject or ""
            if "Cypherpunk Stats" in subject or "Mixmaster Stats" in subject:
                remailers = parse_stats(article.text)
                if remailers:
                    return remailers
    return []


# --- keyring --------------------------------------------------------------

def _session():
    try:
        from unblock_requests import CloudflareSession
        return CloudflareSession(env_prefix="REMAILERS", wayback_fallback=True)
    except ImportError:
        import requests
        return requests.Session()


def fetch_keyring_blob(url: str = KEYRING_URL, timeout: int = 20) -> str:
    """Fetch the published remailer PGP keyring (armored)."""
    resp = _session().get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def load_keyring(blob: str) -> Dict[str, object]:
    """Parse a concatenated keyring blob into {uid_email: PGPKey}."""
    import pgpy

    keys: Dict[str, object] = {}
    first, others = pgpy.PGPKey.from_blob(blob)
    candidates = [first] + [k for k in others.values()
                            if isinstance(k, pgpy.PGPKey)]
    for key in candidates:
        for uid in key.userids:
            if uid.email:
                keys[uid.email.lower()] = key
    return keys


def key_for(remailer: Remailer, keyring: Dict[str, object]):
    """Return the PGP key matching a remailer's address, or None."""
    return keyring.get(remailer.address.lower())
