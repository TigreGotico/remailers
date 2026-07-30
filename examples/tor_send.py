"""Send an anonymous email via Tor.

This example requires:
1. A running Tor daemon listening on 127.0.0.1:9050
2. SMTP credentials (test account on mail.smtp2go.com or similar)

NOTE: This is a placeholder. To run it:
1. Start Tor: `tor` or `sudo systemctl start tor`
2. Update user/pswd with valid SMTP credentials
3. Run: python examples/tor_send.py
"""
from remailers.mail import send_tor_email

if __name__ == "__main__":
    # Placeholder credentials (replace with real ones)
    smtp_user = "anon@mail.smtp2go.com"
    smtp_password = "app-password-here"
    recipient = "test@example.org"

    print("Sending email via Tor SOCKS5 proxy...")
    print(f"Recipient: {recipient}")
    print()

    try:
        send_tor_email(
            user=smtp_user,
            pswd=smtp_password,
            destinatary=recipient,
            subject="Anonymous message",
            contents="This message is sent anonymously through Tor.",
            host="mail.smtp2go.com",
            port=465,
            tor_port=9050  # Default Tor SOCKS port
        )
        print("✓ Email sent successfully")

    except ConnectionRefusedError:
        print("✗ Connection refused on 127.0.0.1:9050")
        print("  Make sure Tor is running: tor")

    except Exception as e:
        print(f"✗ Send failed: {e}")
        print(f"  Check SMTP credentials and network connectivity")
