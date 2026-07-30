# Anonymous Remailer Networks

Anonymous remailers are mail systems that receive messages, strip identifying headers, and forward them to the final recipient—making it impossible for the recipient to learn the sender's address. They form the backbone of anonymous digital communication and have been a core infrastructure for privacy activism, journalism, and research since the 1990s.

## What is a Remailer?

A remailer is a mail server that:

1. **Accepts incoming mail** with no authentication required (or anonymous credentials)
2. **Strips the `From:` and `Return-Path:` headers** so the recipient cannot reply to the sender
3. **Forwards the message to the next hop** or to the final recipient

The sender includes routing instructions in the message body—if it's encrypted, only the remailer (holding the decryption key) can read them. This allows building chains of remailers where each hop knows only the previous and next hop, not the full path.

## The Type-I Cypherpunk Remailer (1992–present)

The original design, proposed by Eric Hughes in 1992, is sometimes called "Type-I" or "Cypherpunk" remailers. They are still operational today.

**How it works:**

1. The sender writes a message and pasting instructions as a `::` block
2. The block is encrypted with PGP to the first remailer's public key
3. That remailer decrypts, reads `Anon-To: <next-address>`, and relays the encrypted payload to the next hop
4. The exit remailer decrypts the final block and reads `Anon-To: <final-recipient>` or `Anon-Post-To: <newsgroup>` to determine where to send it
5. The final message arrives with no sender information

The remailers' public keys and statistics are published daily to the Usenet group `alt.privacy.anon-server.stats` and aggregated at http://echolot.theremailer.net/. Each stats post includes a table of remailers with:

- **Name** (e.g., `dizum`, `frell`)
- **Email address** (e.g., `remailer@dizum.com`)
- **Capability flags** (e.g., `cpunk mix pgp remix latent post`)
- **Latency** (typical delay, e.g., `1.5 days`)
- **Uptime %** (e.g., `99.8%`)

The `remailers.network` module can fetch and parse this:

```python
from remailers.network import fetch_live_remailers, fetch_keyring_blob, load_keyring

# Get the live remailer list
remailers = fetch_live_remailers(server="paganini.bofh.team")
for r in remailers:
    print(f"{r.name}: {r.address} | {r.uptime} uptime | caps: {r.capabilities}")

# Fetch the public keyring
keyring_blob = fetch_keyring_blob()
keyring = load_keyring(keyring_blob)
```

## The Type-II Mixmaster Remailer (1995–present)

Mixmaster remailers use a more sophisticated protocol designed by Lance Cottrell in 1995. They fix problems in Type-I design:

- **Fixed-size packets**: All messages are padded to the same size, defeating traffic analysis by message length
- **Pooling & reordering**: Messages are held and randomly reordered before forwarding, defeating correlation attacks if the same message is sent through multiple hops
- **Better crypto**: Modern algorithms instead of just PGP
- **Latency**: Remailers can delay messages artificially to disguise timing

Mixmaster packets are binary-encoded and carry a chain of encrypted "next-hop" instructions, each encrypted to the next remailer's RSA key. Type-II remailers can also accept Type-I messages (they see the `::` block and process it as Type-I).

The live network includes Type-II remailers like `dizum`, `frell`, and `paranoia`. These remailers support both Type-I and Type-II messages.

**Type-II capability flag:** `mix` in the stats post. If a remailer supports both:

```
cpunk mix pgp ...
```

The remailers library (`remailers.cypherpunk`) builds Type-I messages (Cypherpunk format), not Mixmaster binary packets. Type-I is sufficient for most use cases and avoids the complexity of Mixmaster's fixed-size packet encoding.

## The Type-III Mixminion Remailer (2002–2008)

Mixminion was designed to address limitations in both Type-I and Type-II by Andrei Serjantov and David Goldschlag. It added:

- **Forward secrecy**: Old keys are deleted, so compromise of a remailer's current key doesn't decrypt past messages
- **Reply blocks**: Senders can create a one-time-use reply block and send it to a recipient, allowing the recipient to reply anonymously without knowing the sender's identity
- **Unified protocol**: A single design for all remailers (unlike the Type-I/II split)

Mixminion was never widely deployed and is largely defunct. The design is historically important but not relevant to current operations.

## The Yamn Network (Modern, 2020s)

Yamn ("Yet Another Mix Network") is a modern reimplementation of Mixmaster in Go. It uses the same core idea (fixed-size packets, pooling, reordering) but with:

- **Modern Go code**: Easier to audit and maintain than old C/Perl implementations
- **Better ops**: Container-friendly, easier to deploy and monitor
- **Same protocol**: Compatible with classic Mixmaster clients

Several Yamn nodes operate alongside the older networks. They are visible in the stats posts and can be chained with Type-I or Type-II remailers.

## The Live Network

The remailer network is small but operational:

| Remailer | Address | Type | Uptime | Notes |
|----------|---------|------|--------|-------|
| **dizum** | `remailer@dizum.com` | Type-I/II | ~99% | Highly reliable, supports all caps |
| **frell** | `godot@remailer.frell.eu.org` | Type-I/II | ~95% | Cpunk, mix, pgp, post |
| **yeahno** | `mix@yeahno.net` | Type-II | ~90% | Mix, pgp, latent |
| **frannie** | `mix@franxial.com` | Type-I/II | ~92% | Cpunk, mix, pgp |
| **paranoia** | `mixmaster@remailer.paranoici.org` | Type-I/II | ~98% | Full-featured, hosts nym servers |

All remailers are volunteer-run. The network survives on donations and operators' commitment to privacy. Using the network responsibly (not for spam/abuse) is essential for its survival.

**How to discover live remailers:**

```python
from remailers.network import fetch_live_remailers

remailers = fetch_live_remailers()  # reads alt.privacy.anon-server.stats
for r in remailers:
    if r.is_cpunk and r.accepts_pgp:
        print(f"Suitable for Type-I: {r.name} ({r.uptime})")
```

## Nym Servers and Reply Blocks

A **nym server** (or "pseudonym server") is a service that manages a long-lived anonymous identity for you. Instead of creating a new PGP key for each message, you register with a nym server under a pseudonym, and it stores your public key. Recipients can then send replies to your nym, and the nym server forwards them to you (via another remailer chain or mail-to-news gateway).

The main live nym servers are:

| Service | Domain | Operator |
|---------|--------|----------|
| **IsNotMyName** | `is-not-my.name` | Hosted by various volunteers |
| **MixNym** | `mixnym.net` | Via `remailer.paranoici.org` |
| **Thinhose** | `nym.thinhose.net` | Maintained by `thinhose.net` |

**How nym servers work:**

1. You create a PGP identity (private key only you have)
2. You send a registration request to the nym server (via remailer), encrypted to the nym server's key and including your public key
3. The nym server stores your key under the pseudonym (e.g., `ghostwriter@is-not-my.name`)
4. To receive replies, you subscribe to a reply block or set up mail forwarding
5. Recipients send email to your nym, and the server forwards it to you (anonymously)

The `remailers.zax` module provides client code for nym registration:

```python
from remailers.zax import IsNotMyName

nym = IsNotMyName(alias="ghostwriter")
# Registers with is-not-my.name and stores credentials locally
```

## Network Discovery and Public Keys

The remailer network is self-publishing:

1. **Stats posts**: Published daily to `alt.privacy.anon-server.stats` (e.g., by the Frelled pinger) with all remailer addresses and capabilities
2. **PGP keyring**: Published at http://echolot.theremailer.net/sideview/pgp-all.asc as a concatenated ASCII-armored file containing all remailer public keys
3. **Web pages**: Individual remailers publish their own keys and stats (e.g., `dizum.com`, `remailer.paranoici.org`)

The library fetches from all three:

```python
from remailers.network import (
    fetch_live_remailers, 
    fetch_keyring_blob, 
    load_keyring, 
    key_for
)

# 1. Get the remailer list
remailers = fetch_live_remailers()

# 2. Fetch and parse the keyring
keyring_blob = fetch_keyring_blob()  # from echolot.theremailer.net
keyring = load_keyring(keyring_blob)  # {email → PGPKey}

# 3. Find a key for a specific remailer
remailer = remailers[0]
key = key_for(remailer, keyring)
if key:
    print(f"Found key for {remailer.name}")
```

## Why Remailers Matter

Remailers are a foundational privacy technology:

- **Free speech**: Journalists and dissidents can communicate without fear of surveillance
- **Research**: Cryptographers can test systems without funding from corporations
- **Accessibility**: People with disabilities can participate in discussions without revealing identity
- **Activism**: Whistleblowers and organizers can coordinate safely
- **Academic**: Privacy researchers depend on working remailer infrastructure

The network is operated by volunteers and relies on donations. It is not scalable or fast—messages often take hours or days to arrive—but it is resilient and has survived decades of attacks, law enforcement pressure, and neglect.

## References

- **Frelled/echolot**: http://echolot.theremailer.net/ — live stats and keyring
- **Usenet stats group**: `alt.privacy.anon-server.stats`
- **History**: Eric Hughes, "A Cypherpunk's Manifesto" (1993)
- **Type-II design**: Lance Cottrell, "Mixmaster Protocol" (1995)
- **Type-III (Mixminion)**: Andrei Serjantov & David Goldschlag, "Anonymity in the Wild" (2002)

---
[← API Reference](api-reference.md) · [Home](index.md) · [Architecture →](architecture.md)
