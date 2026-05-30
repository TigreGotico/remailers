# Mix Network Architecture

This document describes how remailers work internally and how they chain together to provide anonymity.

## Single Remailer Behavior

A remailer is a forwarding agent that reads three pieces of information:

1. **Routing instruction** (`Anon-To:` or `Anon-Post-To:` header in the `::` block)
2. **Payload** (the message body or next encrypted block)
3. **Timing instruction** (optional `Latent-Time:` header)

**Processing steps:**

1. Receive a message encrypted to the remailer's PGP key
2. Decrypt it to extract the `::` block
3. Parse the headers (looking for `Anon-To:`, `Anon-Post-To:`, `Latent-Time:`, etc.)
4. Optionally hold the message for the specified latency period
5. Forward the payload to the next hop or final recipient

The sender's identity is never exposed—the remailer only sees the encrypted routing block.

## Onion Routing: Building a Chain

A chain of `n` remailers provides `n` layers of indirection. Each layer is encrypted to the corresponding remailer's public key, and only that remailer can decrypt to learn the next hop.

**Example 2-hop chain:**

Suppose you want to send a message to `alice@example.com` via `dizum` then `frell`:

```
┌─ User (sender)
│
├─ Encrypt 1 (innermost): routing to alice@example.com
│  Create: :: \n Anon-To: alice@example.com \n \n message
│  Encrypt to frell's key → payload_1
│
├─ Encrypt 2: routing to frell, with payload_1 as body
│  Create: :: \n Anon-To: godot@remailer.frell.eu.org \n \n [payload_1]
│  Encrypt to dizum's key → payload_2
│
├─ Send payload_2 to dizum (entry point)
│
├─ dizum receives and decrypts → sees "forward to frell with this encrypted blob"
│  dizum forwards payload_1 to frell
│
└─ frell receives and decrypts → sees "deliver to alice@example.com with this message"
   frell delivers to alice
```

The key insight: **Each hop only knows the previous hop's address and the next hop's address, never the full chain.** This is enforced by encryption—frell can decrypt its layer but cannot decrypt the innermost message to alice.

## Capability Flags

The stats post lists flags for each remailer. These describe what the remailer can do:

| Flag | Meaning |
|------|---------|
| `cpunk` | Supports Type-I Cypherpunk format (`::`  blocks) |
| `mix` | Supports Type-II Mixmaster binary packets |
| `pgp` | Will accept messages encrypted in PGP |
| `pgponly` | Requires PGP encryption (won't accept plaintext `::` blocks) |
| `repgp` | Can re-encrypt to recipients (forward PGP-encrypted messages as-is) |
| `remix` | Can convert Type-I messages to Type-II and chain with Mixmaster |
| `latent` | Supports `Latent-Time:` delays (pooling) |
| `hash` / `hsub` | Hashes subjects with SHA-256 (`hSub`) |
| `esub` / `esubbf` | Encrypts subjects with Blowfish (`eSub`) — legacy |
| `cut` | Recognizes cutmark lines (`[*] [*] [*]`) to strip them |
| `test` | Will accept test messages (a security feature) |
| `ek` / `ekx` | Encrypts key headers (allows encrypted routing info) |
| `inflt` / `inflt50` | Supports inflation (padding) |
| `rhop` | Supports random-hop (will pick next hop randomly) |
| `reord` | Supports reordering/pooling |
| `post` | Can post messages to Usenet newsgroups |
| `klen<N>` | Maximum key length (e.g., `klen64` = 64-bit keys) |
| `max` | Indicates this is the most recent stats |

**Practical guidance:**

- For Type-I chains, require `cpunk` and `pgp` on all hops
- If posting to Usenet, the exit remailer must have `post`
- For latency/pooling, require `latent` and `reord` on hops (except the exit)
- For new code, use `hsub` (hashed subjects) — avoid `esub` (legacy)

The library provides helper properties:

```python
from remailers.network import fetch_live_remailers

remailers = fetch_live_remailers()
for r in remailers:
    if r.is_cpunk and r.accepts_pgp:
        print(f"{r.name} is suitable for Type-I")
    if r.can_post:
        print(f"{r.name} can post to Usenet")
```

## Latency and Pooling

A remailer that supports `latent` and `reord` (reordering) provides traffic-analysis resistance:

1. **Pooling**: The remailer collects incoming messages and holds them for a random period
2. **Reordering**: Instead of immediately forwarding, it randomizes the order of outgoing messages
3. **Padding**: Messages may be padded to the same size

This defeats correlation attacks where an observer watches messages enter and exit the remailer. If messages arrive at `10:00, 10:05, 10:10` and exit at `10:15, 10:20, 10:25` (in the same order), an attacker can match them. Pooling breaks this correspondence.

**How to use latency:**

```python
from remailers.cypherpunk import build_chain

# Request a 2-hour delay on the exit remailer
message, entry_addr = build_chain(
    hops=[...],
    dest="alice@example.com",
    body="secret message",
    latent="2 hours"
)
```

The exit remailer will delay before delivering to `alice`. Intermediate hops that support `latent` can also apply delays.

## Mail-to-News and News-to-Mail Gateways

Some remailers bridge email and Usenet:

- **mail-to-news** (`mail2news@dizum.com`): Accepts an email and posts it to a Usenet newsgroup
- **news-to-mail**: A newsgroup server that accepts posts and relays them via email

The library provides constants:

```python
from remailers.mail import mail2news

# Not yet implemented in the library; see example for manual setup
```

To post to Usenet anonymously:

1. Build a Type-I chain where the exit remailer has `post` capability
2. Instead of `Anon-To: alice@example.com`, use `Anon-Post-To: alt.anonymous.messages`
3. Send to the entry remailer

The final remailer will post to the newsgroup instead of sending email.

## Nym Servers and Reply Blocks

A **nym server** runs on a remailer and manages persistent anonymous identities. It stores:

- Your pseudonym (e.g., `ghostwriter`)
- Your PGP public key
- Reply forwarding instructions (e.g., another remailer chain or email address)

**Workflow:**

1. User generates a PGP key
2. User sends a registration request to the nym server (via remailer), encrypted and signed:
   ```
   Config:
   Nym-Commands: create
   From: ghostwriter
   To:
   
   <user's public key>
   ```
3. Nym server verifies the signature, stores the key, and allocates `ghostwriter@is-not-my.name`
4. Recipients can now send to `ghostwriter@is-not-my.name`
5. The nym server receives their messages, encrypts them to the user's key, and forwards via remailer

The library provides nym registration:

```python
from remailers.zax import IsNotMyName

nym = IsNotMyName(alias="ghostwriter")
nym.register_by_email(
    email="temp_account@gmail.com",
    password="app_password",
    headers={"Remailer": "dizum"}
)
```

## Subject Handling

Subjects are metadata that transit through the remailer network plaintext. To hide them:

**hSub (hashed subject):**

- Uses SHA-256 with a random IV
- One-way: observer cannot recover the original subject
- Deterministic for a given IV: recipient can match by computing the hash
- The `remailers.hsub` module provides `create_hsub` and `match_hsub`

**eSub (encrypted subject, legacy):**

- Uses Blowfish-CFB symmetric encryption with a shared key
- Both parties (sender and recipient) can independently compute the eSub
- Weak by modern standards (Blowfish and MD5 are outdated)
- Exists only for Type-I compatibility; avoid for new code

**Placement:**

When posting to `alt.anonymous.messages`, the subject line of the NNTP article is visible:

```python
from remailers import create_hsub

hsub = create_hsub("meeting time")
# Later, the recipient matches:
from remailers import match_hsub
assert match_hsub(hsub, "meeting time")
```

The actual message body (PGP-encrypted) is separate from the subject, so subjects and bodies can be hidden independently.

## Message Flow: Practical Example

**Scenario:** Alice wants to send a message to Bob via two remailers (`dizum` then `frell`).

1. **Alice generates keys:**
   ```python
   from remailers import Credentials
   creds = Credentials("alice_key.asc")
   ```

2. **Alice builds the chain:**
   ```python
   from remailers.cypherpunk import build_chain
   from remailers.network import fetch_live_remailers, fetch_keyring_blob, load_keyring
   
   remailers = fetch_live_remailers()
   keyring = load_keyring(fetch_keyring_blob())
   
   # Find dizum and frell
   dizum = next(r for r in remailers if r.name == "dizum")
   frell = next(r for r in remailers if r.name == "frell")
   
   # Get their keys from the keyring
   dizum_key = keyring.get(dizum.address.lower())
   frell_key = keyring.get(frell.address.lower())
   
   # Build the chain (dizum → frell → bob@example.com)
   message, entry_addr = build_chain(
       hops=[(dizum.address, dizum_key), (frell.address, frell_key)],
       dest="bob@example.com",
       body="Hello Bob, this is from Alice (anonymously)"
   )
   ```

3. **Alice sends to the entry remailer (dizum):**
   ```python
   from remailers.cypherpunk import send_chain
   
   send_chain(
       message=message,
       entry_address=entry_addr,
       user="alice_smtp_account@example.com",
       password="alice_smtp_password"
   )
   ```

4. **Dizum processes:**
   - Receives message encrypted to its key
   - Decrypts to find `Anon-To: godot@remailer.frell.eu.org`
   - Forwards the inner-encrypted message to frell

5. **Frell processes:**
   - Receives message encrypted to its key
   - Decrypts to find `Anon-To: bob@example.com`
   - Delivers to Bob's mail server

6. **Bob receives:**
   - An email from `no-reply@frell` (or similar) with no sender information
   - The body is the PGP-encrypted message
   - To read it, Bob decrypts using the sender's public key (if he trusts Alice and knows her key)

## See Also

- [Remailer Networks](remailer-networks.md) — overview of live remailers
- [Algorithms](algorithms.md) — detailed message format and encryption
- [Privacy Guarantees](privacy-guarantees.md) — what anonymity is provided
- [Using the Network](using-the-network.md) — practical guide with code examples
