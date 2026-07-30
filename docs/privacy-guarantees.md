# Privacy Guarantees and Threat Model

This document describes what privacy remailers provide, what they do not, and the assumptions required for security.

## What Remailers Protect Against

### Single Malicious Remailer in the Chain

If one remailer in a chain is compromised or malicious:

**Threat:** The malicious operator could log who sends to them and who receives from them.

**Protection:** 

- The malicious remailer sees the sender's IP (if not using Tor) but not the final recipient (thanks to encryption)
- If it's a middle hop, it sees the previous hop's address and the next hop's address, but not the sender or final recipient
- A 3+ hop chain ensures at least two honest remailers exist, so correlation is harder

**Mitigation:**

Use a chain of at least 3 hops, with at least one you trust not to log. Prefer high-uptime, well-known remailers like `dizum` or `frell`. Use Tor to hide your IP from the entry remailer:

```python
from remailers.cypherpunk import send_chain

send_chain(message, entry_address, user, password, tor=True)
```

### Passive Network Eavesdropper

**Threat:** Someone tapping the network sees message traffic.

**Protection:**

- Message bodies are encrypted with PGP (RSA-4096 + AES-256), which is cryptographically unbroken
- SMTP/NNTP connections should use TLS (encrypted in transit)
- Subjects are hidden with hSub (one-way hash) or eSub (symmetric encryption)

**Guarantees:**

An eavesdropper cannot read:

- Message bodies (PGP-encrypted)
- Subjects (hSub is one-way; eSub requires the shared key)
- Routing information (encrypted in the remailer chain)
- Correlation between sender and recipient

An eavesdropper **can** see:

- The sender's IP (if not using Tor)
- The recipient's server (when mail is delivered)
- When messages are sent/received (timing)
- Message size

### Local Observer (ISP or Server Admin)

**Threat:** Your ISP or the mail server you use can see your traffic.

**Protection:**

- PGP encryption hides message bodies (server sees only ciphertext)
- Tor hides your IP from the entry remailer (if using `tor=True`)

**Limitations:**

- The local observer can see when you connect to the remailer network (timing)
- They can see the frequency and size of messages
- Subjects are visible in plaintext SMTP/NNTP if not encrypted by the remailer (hSub/eSub hide from the network, not from the server itself)

**Mitigation:** Use Tor:

```python
from remailers.cypherpunk import send_chain

send_chain(message, entry_address, user, password, tor=True)
```

### Recipient's Server Admin

**Threat:** The recipient's mail server admin can read messages and log who sends to them.

**Protection:**

- Message body is encrypted to the recipient's PGP key (only they can decrypt)
- Sender's identity is hidden (no `From:` header from the remailer)

**Limitations:**

- The recipient's server sees the subject line (plaintext SMTP)
- The recipient's server sees when messages arrive (timing)
- If the recipient logs NNTP access, they see who retrieves messages from newsgroups

**Mitigation:**

- Encrypt the subject (hSub/eSub hide it from network observers, but not from NNTP servers)
- Use PGP body encryption (default)

## What Remailers Do NOT Protect Against

### Global Passive Adversary

**Threat:** An attacker controls the network and can see all traffic.

**Limitation:**

While message bodies are encrypted, the adversary can perform **traffic analysis**:

1. **Intersection attacks:** By observing many messages over time, deduce sender-recipient pairs from timing and size correlations
2. **Timing attacks:** If only one person sends to a remailer at 3:00 PM, and one person receives from it at 3:30 PM, the adversary can guess a correlation
3. **Message size:** Messages of unique sizes can be tracked across hops

**Mitigation:**

- Use pooling and reordering (`latent` remailers delay and randomize order)
- Pad messages to fixed sizes (Type-II Mixmaster; Type-I does not do this automatically)
- Send many dummy messages to create noise
- Vary timing artificially

**Theoretical limit:** No single remailer system can defeat a true global passive adversary. This is a fundamental limit of any communication system.

### Endpoint Compromise

**Threat:** Your computer is compromised (virus, malware, keylogger).

**Limitation:**

All encryption is pointless if the attacker has your private key and plaintext messages.

**Mitigation:**

- Keep your operating system and software updated
- Use a dedicated machine for anonymous messaging
- Protect your PGP private key with a strong passphrase
- Never use the same identity on multiple systems

### Message Content Analysis

**Threat:** The recipient (or their server) can analyze the plaintext message and identify the sender.

**Limitation:**

Remailers hide *who* sends a message, not *what* it says. Stylometry (writing style analysis) can sometimes identify authors. Unique information in the message can unmask the sender.

**Mitigation:**

- Vary your writing style
- Avoid referencing personal details
- Use generic language
- Write as if multiple people could have sent the message

### Intersection and Timing Attacks

**Threat:** Over many messages, an attacker can correlate sender and recipient by observing message patterns.

**Example:**

Alice always sends to Bob at 3:00 PM UTC. An attacker observes:
- Messages enter `dizum` at 3:00 PM (always the same time)
- Messages exit from `frell` at 3:15 PM (always the same time)
- Same size each time

Over many days, the attacker deduces that Alice (entry at 3:00) corresponds to Bob (exit at 3:15).

**Mitigation:**

- Use variable latency (`latent` remailers with random delays)
- Send messages at different times of day
- Vary message sizes (pad or truncate)
- Send decoy messages
- Use long remailer chains (3+ hops)

### Forward Secrecy

**Threat:** Your PGP private key is compromised in the future.

**Limitation:**

All messages encrypted to your key can be decrypted retroactively.

**Mitigation:**

- Rotate your PGP key periodically
- Securely delete old private keys after rotation
- Consider using a "one-shot" key per message or conversation

### Nym Server Operator

**Threat:** The nym server operator can read registration requests, replies, and deduce your identity.

**Limitation:**

If the nym server is run by an adversary, they can:
- See all registrations and their embedded public keys
- See all reply messages before forwarding
- Link your nym to your mail server IP (unless you use Tor)

**Mitigation:**

- Use a nym server you trust (volunteer-run, well-known)
- Send registration and replies via a remailer chain over Tor
- Register from an anonymous email account (not your real identity)

## Anonymity Set and Mixing

The strength of a remailer chain depends on the **anonymity set** — the number of other users using the same remailer(s) at the same time.

**Small anonymity set (e.g., 5 users):**
- An observer can correlate messages easier (fewer possibilities)
- Timing attacks are more effective
- Intersection attacks work better

**Large anonymity set (e.g., 1000 users):**
- Correlation requires more work (more possibilities)
- Timing attacks less effective (noise from others)
- Intersection attacks less reliable

**Impact on library:**

The library doesn't track anonymity set size, but you should:

- Prefer high-traffic remailers (`dizum`, `paranoia`)
- Use them during peak hours (when many others are using them)
- Check stats for uptime and recent traffic

## Assumptions Required for Security

For remailers to provide anonymity, these assumptions must hold:

1. **Honest remailers exist:** At least some remailers in the chain do not log traffic
2. **PGP is unbroken:** RSA-4096 and AES-256 remain secure (no practical breaks)
3. **The network is not fully observable:** An attacker cannot monitor all network traffic everywhere
4. **Remailers execute correctly:** The software processes messages as designed (no backdoors)
5. **Your SMTP sender is not logged:** The mail account you use to send doesn't log your IP or reveal your identity
6. **Tor (if used) is secure:** Tor's anonymity properties hold
7. **You don't leak your identity elsewhere:** Your nym account, PGP key, and communication patterns don't link back to you

If any assumption fails, anonymity degrades.

## Threat Model Summary

| Adversary | Sender Anonymous? | Recipient Anonymous? | Message Private? | Protection |
|-----------|------------------|----------------------|------------------|------------|
| Passive eavesdropper | Yes (chain) | Yes (chain + encryption) | Yes (PGP) | Chain + PGP + Tor |
| ISP / local observer | No (unless Tor) | Yes (chain) | Yes (PGP) | Tor + PGP |
| Single remailer | Partial (others hops hide) | Yes (chain) | Yes (PGP) | Multi-hop chain + PGP |
| Global passive adversary | No (timing analysis) | No (timing analysis) | Yes (PGP) | Pooling + padding + timing noise |
| Recipient's server | Yes (remailer strips `From:`) | No (on their server) | Yes (PGP) | Recipient must decrypt privately |
| Compromised endpoint | No | No | No | Keep system clean |
| Nym server (untrusted) | No (registration IP logged) | No (can read replies) | Yes (PGP) | Trust the nym operator; use Tor |

## Best Practices

1. **Use a chain of 3+ remailers** — Protects against single malicious remailer
2. **Prefer high-uptime remailers** — Larger anonymity set, less likely to be honeypots
3. **Always use PGP body encryption** — Protects message content
4. **Use Tor for entry message** — Hides your IP from the entry remailer
5. **Vary timing and message size** — Defeats timing/size correlation attacks
6. **Don't reuse subjects across identities** — Prevents linking identities
7. **Rotate keys periodically** — Limits exposure if a key is compromised
8. **Use hSub for subjects** — Modern, one-way hiding (eSub is legacy)
9. **Test locally first** — Verify encryption round-trips before sending live
10. **Document assumptions** — Understand what you're trusting

## Limitations of This Library

- The library builds **Type-I messages only**, not Type-II Mixmaster packets (which have fixed-size and pooling)
- **No artificial padding** — Type-I messages vary in size; use `latent` remailers for timing noise
- **Subject hiding is metadata only** — Remailer servers still see plaintext subjects (though network observers see hSub)
- **No nym server protocol validation** — ZAX registration is basic; real nym servers may require more checks
- **No built-in decoy traffic** — You must manually send dummy messages for noise

For maximum privacy:

- Build 3+ hop chains using well-known remailers
- Always encrypt bodies with PGP
- Use Tor for SMTP if possible
- Use `latent` remailers with variable delays
- Monitor the network for operator/reliability changes

---
[← Algorithms](algorithms.md) · [Home](index.md) · [Using the Network →](using-the-network.md)
