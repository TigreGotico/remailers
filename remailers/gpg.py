"""GnuPG backend for encrypting to real remailer keys.

The live remailer network uses DSA primary keys with ElGamal encryption
subkeys. PGPy cannot encrypt to ElGamal, so messages destined for actual
remailers are encrypted by shelling out to GnuPG, which handles those keys
natively. Our own RSA identity (remailers.keys.Credentials) still uses PGPy.
"""
import os
import shutil
import subprocess
import tempfile
from typing import List, Optional


def gpg_available() -> bool:
    """True if a usable `gpg` binary is on PATH."""
    exe = shutil.which("gpg")
    if not exe:
        return False
    try:
        subprocess.run([exe, "--version"], capture_output=True, check=True)
        return True
    except (OSError, subprocess.CalledProcessError):
        return False


class GPGKeyring:
    """A throwaway GnuPG home seeded with a keyring blob.

    Use as a context manager; the temporary home is removed on exit.
    """

    def __init__(self, keyring_blob: str, gpg_bin: Optional[str] = None):
        self.gpg = gpg_bin or shutil.which("gpg")
        if not self.gpg:
            raise RuntimeError("gpg not found on PATH")
        self.home = tempfile.mkdtemp(prefix="remailers-gpg-")
        self._import(keyring_blob)

    def _run(self, args: List[str], data: Optional[bytes] = None) -> subprocess.CompletedProcess:
        env = dict(os.environ, GNUPGHOME=self.home)
        return subprocess.run(
            [self.gpg, "--batch", "--no-tty", "--yes"] + args,
            input=data, capture_output=True, env=env)

    def _import(self, blob: str) -> None:
        result = self._run(["--import"], blob.encode("utf-8", "replace"))
        if result.returncode != 0:
            raise RuntimeError(f"gpg import failed: {result.stderr.decode()[-200:]}")

    def recipients(self) -> List[str]:
        """Email addresses of imported keys."""
        result = self._run(["--list-keys", "--with-colons"])
        emails = []
        for line in result.stdout.decode("utf-8", "replace").splitlines():
            if line.startswith("uid"):
                uid = line.split(":")[9]
                if "<" in uid and ">" in uid:
                    emails.append(uid.split("<", 1)[1].split(">", 1)[0])
        return emails

    def encrypt(self, recipient: str, plaintext: str) -> str:
        """Return an ASCII-armored message encrypted to `recipient`."""
        data = plaintext.encode("utf-8") if isinstance(plaintext, str) else plaintext
        result = self._run(
            ["--trust-model", "always", "--armor",
             "--encrypt", "--recipient", recipient], data)
        if result.returncode != 0:
            raise RuntimeError(
                f"gpg encrypt to {recipient} failed: {result.stderr.decode()[-200:]}")
        return result.stdout.decode("utf-8")

    def close(self) -> None:
        shutil.rmtree(self.home, ignore_errors=True)

    def __enter__(self) -> "GPGKeyring":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()
