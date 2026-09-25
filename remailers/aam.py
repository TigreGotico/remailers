from remailers.keys import PGPError
from remailers import match_esub, match_hsub


class AnonBox:
    GROUP = 'alt.anonymous.messages'

    def __init__(self, creds, usenet_server, esub_key=None):
        self.creds = creds
        self.usenet_server = usenet_server
        self.esub_key = esub_key

    def _decrypt_into(self, article):
        """Decrypt the article body in place; return True on success."""
        decrypted = self.creds.decrypt(article.text)
        article._body = [line.encode("utf-8")
                         for line in decrypted.split("\n")]
        return True

    def retrieve(self, limit=50):
        """Pull the latest `limit` messages and keep the ones we can decrypt.

        Browses by GROUP rather than NEWNEWS, which public servers disable.
        """
        articles = []
        with self.usenet_server as server:
            for article in server.get_articles(self.GROUP, limit=limit):
                if "BEGIN PGP MESSAGE" not in article.text:
                    continue
                try:
                    self._decrypt_into(article)
                    articles.append(article)
                except (PGPError, ValueError):
                    continue
        return articles

    def retrieve_by_subject(self, subject, limit=200, esubs=True, hsubs=True):
        """Keep messages whose subject matches `subject` directly or via an
        hSub/eSub, and that decrypt with our key."""
        articles = []
        with self.usenet_server as server:
            for article in server.get_articles(self.GROUP, limit=limit):
                matched = (
                    subject == article.subject
                    or (hsubs and match_hsub(article.subject, subject))
                    or (esubs and self.esub_key
                        and match_esub(subject, self.esub_key, article.subject))
                )
                if not matched:
                    continue
                try:
                    self._decrypt_into(article)
                    articles.append(article)
                except (PGPError, ValueError):
                    continue  # subject matched, but not encrypted to our key
        return articles
