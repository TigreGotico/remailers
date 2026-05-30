import pgpy
from pgpy.constants import *
from pgpy.errors import PGPError
from datetime import datetime, timedelta
from os.path import isfile


def export_private_key(path, key=None, binary=False, *args, **kwargs):
    key = key or create_private_key(*args, **kwargs)
    if binary:
        with open(path, "wb") as f:
            f.write(bytes(key))
    else:
        with open(path, "w") as f:
            f.write(str(key))


def create_private_key(name="MyRemailerKey", email=None, expires=None):
    key = pgpy.PGPKey.new(PubKeyAlgorithm.RSAEncryptOrSign, 4096)
    uid = pgpy.PGPUID.new(name, email=email)
    if isinstance(expires, timedelta):
        expires = datetime.now() + expires
    key.add_uid(uid,
                usage={KeyFlags.Sign,
                       KeyFlags.EncryptCommunications},
                hashes=[HashAlgorithm.SHA512,
                        HashAlgorithm.SHA256],
                ciphers=[SymmetricKeyAlgorithm.AES256,
                         SymmetricKeyAlgorithm.Camellia256],
                compression=[CompressionAlgorithm.BZ2,
                             CompressionAlgorithm.ZIP,
                             CompressionAlgorithm.Uncompressed],
                expiry_date=expires)
    return key


def read_key(key_blob):
    key, _ = pgpy.PGPKey.from_blob(key_blob)
    return key


def encrypt_text(key, text, creds=None):
    if not isinstance(key, pgpy.PGPKey):
        key = read_key(key)
    text_message = pgpy.PGPMessage.new(text)
    # encrypt generated key
    encrypted_message = key.encrypt(text_message)
    if creds:
        # sign message
        # the bitwise OR operator '|' is used to add a signature to a PGPMessage.
        encrypted_message |= creds.sign(encrypted_message,
                                        intended_recipients=[key])
    return str(encrypted_message)


class Credentials:
    def __init__(self, path, name=None, email=None, expires=None):
        if path.endswith(".asc") or path.endswith(".txt"):
            binary = False
        else:
            binary = True
        if isfile(path):
            self.load_private(path, binary=binary)
        else:
            name = name or path.split("/")[-1].split(".")[0]
            self.private_key = create_private_key(name=name,
                                                  email=email,
                                                  expires=expires)
            if path:
                export_private_key(path, key=self.private_key, binary=binary)

    def load_private(self, path, binary=False):
        if binary:
            with open(path, "rb") as f:
                key_blob = f.read()
        else:
            with open(path, "r") as f:
                key_blob = f.read()
        self.private_key = self.import_key(key_blob)

    @property
    def pubkey(self):
        if not self.private_key:
            return None
        return str(self.private_key.pubkey)

    @staticmethod
    def import_key(key_blob):
        return read_key(key_blob)

    def decrypt(self, encrypted_message):
        message = pgpy.PGPMessage.from_blob(encrypted_message)
        return self.private_key.decrypt(message).message

    def encrypt(self, txt, key=None):
        key = key or self.pubkey
        return encrypt_text(key, txt)

    def sign(self, message, intended_recipients=None):
        return self.private_key.sign(message,
                                     intended_recipients=intended_recipients)

