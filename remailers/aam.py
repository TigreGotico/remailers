from remailers.keys import PGPError
from remailers import match_esub, match_hsub


class AnonBox:
    GROUP = 'alt.anonymous.messages'

    def __init__(self, creds, usenet_server, esub_key=None):
        self.creds = creds
        self.usenet_server = usenet_server
        self.esub_key = esub_key

    def retrieve(self, since=None):
        articles = []
        with self.usenet_server as server:
            for article in server.get_new_news(self.GROUP, since=since):
                if "BEGIN PGP MESSAGE" in article.text:
                    article.headers  # retrieve while connection is open
                    try:
                        decrypted = self.creds.decrypt(article.text)
                        article._body = [l.encode("utf-8")
                                         for l in decrypted.split("\n")]
                        articles.append(article)
                    except (PGPError, ValueError):
                        continue
        # TODO sort by date
        return articles

    def retrieve_by_subject(self, subject, since=None, esubs=True, hsubs=True):
        articles = []
        with self.usenet_server as server:
            for article in server.get_new_news(self.GROUP, since=since):
                try:
                    if subject == article.subject:
                        decrypted = self.creds.decrypt(article.text)
                        article._body = [l.encode("utf-8")
                                         for l in decrypted.split("\n")]
                        articles.append(article)
                        continue
                    if hsubs and match_hsub(article.subject, subject):
                        decrypted = self.creds.decrypt(article.text)
                        article._body = [l.encode("utf-8")
                                         for l in decrypted.split("\n")]
                        articles.append(article)
                        continue
                    if esubs and self.esub_key:
                        if match_esub(subject, self.esub_key, article.subject):
                            decrypted = self.creds.decrypt(article.text)
                            article._body = [l.encode("utf-8")
                                             for l in decrypted.split("\n")]
                            articles.append(article)
                            continue
                except (PGPError, ValueError):
                    pass  # same subject, but not using our key
        # TODO sort by date
        return articles
