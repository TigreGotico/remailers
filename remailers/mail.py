import socket
import socks
from smtplib import SMTP, SMTP_SSL


class SocksSMTP(SMTP):

    def __init__(self,
                 host='',
                 port=0,
                 local_hostname=None,
                 timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=None,
                 proxy_type=None,
                 proxy_addr=None,
                 proxy_port=None,
                 proxy_rdns=True,
                 proxy_username=None,
                 proxy_password=None,
                 socket_options=None):

        self.proxy_type = proxy_type
        self.proxy_addr = proxy_addr
        self.proxy_port = proxy_port
        self.proxy_rdns = proxy_rdns
        self.proxy_username = proxy_username
        self.proxy_password = proxy_password
        self.socket_options = socket_options
        # if proxy_type is provided then change the socket to socksocket
        # behave like a normal SMTP class.
        if self.proxy_type:
            self._get_socket = self.socks_get_socket

        super(SocksSMTP, self).__init__(host, port, local_hostname, timeout,
                                        source_address)

    def socks_get_socket(self, host, port, timeout):
        if self.debuglevel > 0:
            self._print_debug('connect: to', (host, port), self.source_address)
        return socks.create_connection((host, port),
                                       timeout=timeout,
                                       source_address=self.source_address,
                                       proxy_type=self.proxy_type,
                                       proxy_addr=self.proxy_addr,
                                       proxy_port=self.proxy_port,
                                       proxy_rdns=self.proxy_rdns,
                                       proxy_username=self.proxy_username,
                                       proxy_password=self.proxy_password,
                                       socket_options=self.socket_options)


class TorSMTP(SocksSMTP):
    def __init__(self, host, port=25, timeout=socket._GLOBAL_DEFAULT_TIMEOUT,
                 source_address=None, socket_options=None, tor_port=9050):
        super().__init__(host, port,
                         timeout=timeout, source_address=source_address,
                         proxy_type=socks.SOCKS5,
                         proxy_addr="127.0.0.1",
                         proxy_port=tor_port, socket_options=socket_options)


def build_message(sent_from, to, subject, body):
    """Assemble an RFC-822 message. Header lines must not be indented, or the
    leading whitespace folds them into the previous header's value."""
    recipients = ", ".join(to)
    return (
        f"From: {sent_from}\r\n"
        f"To: {recipients}\r\n"
        f"Subject: {subject}\r\n"
        f"\r\n"
        f"{body}\r\n"
    )


def _send(server, user, destinatary, subject, contents):
    to = [destinatary]
    email_text = build_message(user, to, subject, contents)
    server.sendmail(user, to, email_text)
    server.close()


def send_email(user, pswd, destinatary, subject, contents,
               host="mail.smtp2go.com", port=465, ssl=True):
    if ssl:
        server = SMTP_SSL(host=host, port=port)
    else:
        server = SMTP(host=host, port=port)
    server.ehlo()
    server.login(user, pswd)
    return _send(server, user, destinatary, subject, contents)


def send_tor_email(user, pswd, destinatary, subject, contents,
                   host="mail.smtp2go.com", port=465):
    server = TorSMTP(host=host, port=port)
    server.ehlo()
    server.login(user, pswd)
    return _send(server, user, destinatary, subject, contents)


def mail2news():
    # mail2news@dizum.com
    # mail2news@neodome.net
    # mail2news@m2n.mixmin.net
    raise NotImplementedError
