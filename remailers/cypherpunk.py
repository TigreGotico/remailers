"""Build Type-I (Cypherpunk) remailer messages.

A Cypherpunk remailer reads a message whose body is a "pasting-token" block:

    ::
    Encrypted: PGP

    -----BEGIN PGP MESSAGE-----
    ...
    -----END PGP MESSAGE-----

Decrypting that yields another ``::`` block of instructions — ``Anon-To:`` to
relay to the next hop or final recipient, ``Anon-Post-To:`` to post to a
newsgroup, ``Latent-Time:`` to delay. Nesting these, each layer encrypted to the
next remailer's key, forms the onion that hides the path. This module assembles
that onion; sending the entry message is left to :mod:`remailers.mail`.
"""
from typing import List, Optional, Sequence, Tuple

from remailers.keys import encrypt_text


def _block(headers: dict, body: str = "") -> str:
    lines = ["::"]
    for key, value in headers.items():
        lines.append(f"{key}: {value}")
    lines.append("")  # blank line terminates the header block
    if body:
        lines.append(body)
    return "\n".join(lines)


def final_request(dest: Optional[str] = None, anon_post_to: Optional[str] = None,
                  body: str = "", latent: Optional[str] = None,
                  extra_headers: Optional[dict] = None) -> str:
    """Build the innermost instruction block delivered by the exit remailer.

    Provide ``dest`` (email) or ``anon_post_to`` (newsgroup).
    """
    if not dest and not anon_post_to:
        raise ValueError("final_request needs dest or anon_post_to")
    headers = {}
    if dest:
        headers["Anon-To"] = dest
    if anon_post_to:
        headers["Anon-Post-To"] = anon_post_to
    if latent:
        headers["Latent-Time"] = latent
    if extra_headers:
        headers.update(extra_headers)
    return _block(headers, body)


def wrap_encrypted(remailer_key, inner: str) -> str:
    """Encrypt ``inner`` to a remailer's PGP key and wrap it for that remailer."""
    ciphertext = encrypt_text(remailer_key, inner)
    return _block({"Encrypted": "PGP"}, ciphertext)


def build_chain(hops: Sequence[Tuple[str, object]], dest: Optional[str] = None,
                anon_post_to: Optional[str] = None, body: str = "",
                latent: Optional[str] = None, encrypt=None) -> Tuple[str, str]:
    """Assemble a nested Cypherpunk message through a chain of remailers.

    ``hops`` is an ordered sequence of ``(address, recipient)`` from entry to
    exit. ``encrypt(recipient, plaintext) -> armored`` does each layer; it
    defaults to PGPy (``recipient`` is a ``PGPKey``). To reach the real network
    (DSA/ElGamal keys), pass a GnuPG encryptor — e.g. ``GPGKeyring.encrypt`` with
    ``recipient`` set to each remailer's address. Returns ``(message,
    entry_address)`` — send ``message`` to ``entry_address``.
    """
    if not hops:
        raise ValueError("need at least one remailer hop")
    if encrypt is None:
        encrypt = encrypt_text
    inner = final_request(dest=dest, anon_post_to=anon_post_to,
                          body=body, latent=latent)
    message = None
    next_addr = None
    # build from the exit hop inward
    for address, recipient in reversed(list(hops)):
        if message is None:
            payload = inner                       # exit hop delivers to dest
        else:
            payload = _block({"Anon-To": next_addr}, message)  # relay to next hop
        message = _block({"Encrypted": "PGP"}, encrypt(recipient, payload))
        next_addr = address
    return message, hops[0][0]


def send_chain(message: str, entry_address: str, user: str, password: str,
               host: str = "mail.smtp2go.com", port: int = 465,
               tor: bool = False) -> None:
    """Deliver an assembled message to the entry remailer over SMTP.

    Needs an email sender (any account, or a Tor-routed SMTP with ``tor=True``).
    """
    from remailers.mail import send_email, send_tor_email

    sender = send_tor_email if tor else send_email
    sender(user, password, entry_address, subject="", contents=message,
           host=host, port=port)
