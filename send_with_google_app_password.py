"""send_with_google_app_password.py

Retrieve the Google App password from Windows Credential Manager (keyring) and call
the project's `send_email` function in `SmartFindScript.py`.

This script looks for a credential with username 'SmartFindAutomationGoogleApp'.
If found, it will call send_email(to, subject, body, from_address=..., password=...)
using Gmail's SMTP defaults (smtp.gmail.com:587).

Do NOT store plain secrets in source control. This script reads the secret from
Windows Credential Manager via the keyring library.
"""

import logging
import sys
import keyring

# Import the send_email function from the existing module in the same folder.
try:
    from SmartFindScript import send_email
except Exception as e:
    raise ImportError("Could not import send_email from SmartFindScript.py: " + str(e))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')


def find_app_password(service_name: str, username: str):
    """Retrieve the password from Windows Credential Manager using the specified service name and username.

    Returns the password string or None if not found.
    """
    try:
        pwd = keyring.get_password(service_name, username)
    except Exception:
        pwd = None
    if pwd:
        logger.info("Found credential using service=%s username=%s", service_name, username)
        return pwd
    return None


def main():
    google_app_service = "SmartFindAutomationGoogleApp"
    service_username = "SmartFindAutomation"
    to_address = "rwsimmo@gmail.com, simm.sean16@gmail.com"
    from_address = "rwsimmo@gmail.com"
    subject = "SmartFindAutomation: test email"
    body = ("This is a test email sent by SmartFindAutomation using the Google App "
            "password stored in Windows Credential Manager.")

    password = find_app_password(google_app_service, service_username)
    if not password:
        logger.error("Google App password for service_username '%s' not found in Credential Manager.", 
                     service_username)
        logger.error("Please add it to Windows Credential Manager (use Windows Credential Manager UI or keyring.set_password) and try again.")
        sys.exit(1)

    logger.info("Calling send_email to send a test message to %s", to_address)
    try:
        ok = send_email(to_address, subject, body, from_address=from_address, password=password)
    except Exception as exc:
        logger.exception("send_email raised an exception: %s", exc)
        sys.exit(2)

    if ok:
        logger.info("Email sent successfully to %s", to_address)
        sys.exit(0)
    else:
        logger.error("send_email reported failure")
        sys.exit(3)


if __name__ == "__main__":
    main()
