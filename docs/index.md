# remailers documentation

This directory contains guides and API reference for anonymous messaging with PGP over Usenet and Tor email.

## Quick Navigation

- **[README](../README.md)** - package overview and security notes
- **[Quickstart](quickstart.md)** - five-minute introduction to generating identities and hashed subjects
- **[Identities](identities.md)** - Credentials, generating and loading PGP keys
- **[Subjects](subjects.md)** - hSub (hashed subject) and eSub (encrypted subject), when to use each
- **[AnonBox](anonbox.md)** - post PGP-encrypted messages to alt.anonymous.messages and retrieve by subject

- **[Tor Email](tor-email.md)** - send anonymous email via Tor with SocksSMTP and TorSMTP
- **[ZAX Nym Servers](zax-nyms.md)** - nym server registration (experimental)
- **[Security](security.md)** - cryptography details, IV entropy, and threat model
- **[API Reference](api-reference.md)** - concise symbol reference for all public APIs

## The remailer network

- **[Remailer Networks](remailer-networks.md)** - the live Cypherpunk/Mixmaster/Yamn network, its lineage, and discovery
- **[Architecture](architecture.md)** - mix networks, chaining, latency/pooling, gateways, nym servers
- **[Algorithms](algorithms.md)** - the Type-I `::` onion format, hSub/eSub, key types (DSA/ElGamal)
- **[Privacy Guarantees](privacy-guarantees.md)** - threat model, anonymity set, and honest limitations
- **[Using the Network](using-the-network.md)** - discover live remailers, build a chain, send

## Related Projects

The **[usenet](../../usenet/docs/index.md)** package provides the underlying NNTP client and newsgroup infrastructure that remailers builds on. Read articles from Usenet, discover public NNTP servers, and harvest text corpora.

## Note

This toolkit is for research and privacy education. The Cypherpunk/Mixmaster
remailer network is still operating, with a handful of active remailers and
nym servers tracked live via `remailers.network`.

The network is small. Treat it accordingly, and read
[Privacy Guarantees](privacy-guarantees.md) before relying on it. Encrypting
to the live network's DSA/ElGamal keys requires the GnuPG backend
(`remailers.gpg`).
