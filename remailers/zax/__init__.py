import requests
from remailers import Credentials
from remailers.mail import send_email
from remailers.keys import encrypt_text


class ZAX:
    homepage = None
    domain = None
    key_url = None
    _pubkey = None

    def __init__(self, credentials=None, alias="PythonicAnon"):
        self.alias = alias
        self.credentials = credentials or self.get_default_credentials()
        self.get_nym_pubkey()

    def get_default_credentials(self):
        email = self.alias + "@" + self.domain
        path = email + ".asc"
        return Credentials(path, self.alias, email)

    @property
    def config_mail(self):
        return "config@" + self.domain

    @property
    def send_mail(self):
        return "send@" + self.domain

    @property
    def list_mail(self):
        return "list@" + self.domain

    @property
    def key_mail(self):
        return "remailer-key@" + self.domain

    @classmethod
    def get_nym_pubkey(cls):
        if not cls._pubkey:
            r = requests.get(cls.key_url, timeout=15)
            if r.status_code == 200:
                cls._pubkey = r.text
        return cls._pubkey

    def get_key_by_email(self, email, password):
        return send_email(email, password,
                          subject="", contents="",
                          destinatary=self.key_mail)

    # TODO remailer/mixmaster option
    def register_by_email(self, email, password, headers=None):
        headers = headers or {}
        lines = ["Config:", "Nym-Commands: create"]
        for k, v in headers.items():
            lines.append(k + ": " + v)
        body = "\n".join(lines) + "\n" + self.credentials.pubkey
        body = encrypt_text(self.get_nym_pubkey(), body,
                            creds=self.credentials)
        return send_email(email, password,
                          subject="", contents=body,
                          destinatary=self.config_mail)

    def remail_by_email(self, email, password, destinatary,
                        subject="anon message", body="this is a test",
                        headers=None):
        headers = headers or {}
        headers["From"] = ""
        headers["To"] = destinatary
        headers["Subject"] = subject
        msg = ""
        for k, v in headers.items():
            msg += k + ": " + v + "\n"
        msg += body
        # encrypt to nym server + sign
        body = encrypt_text(self.get_nym_pubkey(), msg,
                            creds=self.credentials)
        return send_email(email, password,
                          subject="", contents=body,
                          destinatary=self.send_mail)


class IsNotMyName(ZAX):
    homepage = "https://remailer.paranoici.org/nym.php"
    domain = "is-not-my.name"
    key_url = "http://is-not-my.name/key.asc"


class MixNym(ZAX):
    homepage = "https://remailer.paranoici.org/nym.php"
    key_url = "http://remailer.paranoici.org/nymphet.asc"
    domain = "mixnym.net"


class Thinhose(ZAX):
    homepage = "nym.thinhose.net"
    key_url = "https://thinhose.net/key.asc"
    domain = "nym.thinhose.net"
