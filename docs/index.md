# remailers documentation

This directory contains guides and API reference for anonymous messaging with PGP over Usenet and Tor email.

## Quick Navigation

- **[README](../README.md)** — package overview and security notes
- **[Quickstart](quickstart.md)** — five-minute introduction to generating identities and hashed subjects
- **[Identities](identities.md)** — Credentials, generating and loading PGP keys
- **[Subjects](subjects.md)** — hSub (hashed subject) and eSub (encrypted subject) – when to use each
- **[AnonBox](anonbox.md)** — post PGP-encrypted messages to alt.anonymous.messages and retrieve by subject
- **[Tor Email](tor-email.md)** — send anonymous email via Tor with SocksSMTP and TorSMTP
- **[ZAX Nym Servers](zax-nyms.md)** — nym server registration (experimental/historical)
- **[Security](security.md)** — cryptography details, IV entropy, and threat model
- **[API Reference](api-reference.md)** — concise symbol reference for all public APIs

## Related Projects

The **[usenet](../../usenet/docs/index.md)** package provides the underlying NNTP client and newsgroup infrastructure that remailers builds on. Read articles from Usenet, discover public NNTP servers, and harvest text corpora.

## Security Disclaimer

This toolkit is for research and privacy education. The public nym/remailer network is largely historical; bundled server definitions should be treated as starting points. Treat the package as deprecated infrastructure for archive/educational purposes only.
