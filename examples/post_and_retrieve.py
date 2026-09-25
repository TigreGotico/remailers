"""Post an encrypted message to alt.anonymous.messages and retrieve it.

This example requires a live NNTP server and PGP key.

NOTE: To run this example:
1. Have an active NNTP server connection
2. Generate a key: python examples/generate_identity.py
3. Adjust SERVER and GROUP if using a different server
"""
from usenet import UsenetServer
from remailers import Credentials, AnonBox, create_hsub

# Configure these for your server
SERVER = "news.eternal-september.org"  # or another public server
GROUP = "alt.anonymous.messages"

if __name__ == "__main__":
    # Load PGP credentials
    creds = Credentials("anon.asc", name="PythonicGhost")

    # Create a hashed subject (hiding the actual message code)
    plaintext_subject = "secret rendezvous alpha"
    hsub = create_hsub(plaintext_subject)

    # Message to send
    plaintext_message = "Meet at the old mill at 3 PM."
    ciphertext = creds.encrypt(plaintext_message)

    print(f"Posting to {GROUP}...")
    print(f"Subject (hashed): {hsub}")
    print()

    # Post the encrypted message
    post_success = True
    try:
        with UsenetServer(SERVER) as server:
            server.post(
                text=ciphertext,
                subject=hsub,
                group=GROUP
            )
        print("✓ Message posted")
    except Exception as e:
        print(f"Post failed (server may not allow posting): {e}")
        post_success = False

    if not post_success:
        print("Skipping retrieval due to post failure")
    else:
        print()
        print("Retrieving messages from alt.anonymous.messages...")

        # Retrieve and decrypt
        try:
            inbox = AnonBox(creds, UsenetServer(SERVER))
            articles = inbox.retrieve_by_subject(
                plaintext_subject,
                hsubs=True,
                esubs=False
            )

            print(f"Found {len(articles)} matching messages")
            for article in articles:
                print(f"\nFrom: {article.author}")
                print(f"Date: {article.date}")
                print(f"Subject: {article.subject}")
                print(f"Message: {article.text[:200]}")

        except Exception as e:
            print(f"Retrieval failed: {e}")
