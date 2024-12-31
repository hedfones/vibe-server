from base64 import urlsafe_b64encode
from email.mime.text import MIMEText

import structlog

from .auth import GoogleServiceBase

log = structlog.stdlib.get_logger()


class GoogleGmail(GoogleServiceBase["GoogleGmail"]):
    api_name: str = "gmail"
    api_version: str = "v1"

    def send_email(self, to: str, subject: str, body: str) -> None:
        """
        Sends an email via Gmail.

        Args:
            to (str): Recipient email address.
            subject (str): Subject of the email.
            body (str): Body of the email.
        """
        message = MIMEText(body)
        message["to"] = to
        message["subject"] = subject
        raw_message = urlsafe_b64encode(message.as_bytes()).decode()

        try:
            self.service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
            log.info(f"Email sent to {to}")
        except Exception:
            log.exception("An error occurred while sending the email.")

    def list_emails(self, query: str = "") -> list[dict[str, str]]:
        """
        Lists emails in the user's Gmail inbox.

        Args:
            query (str): String used to filter the emails using Gmail API. (e.g., 'is:unread')

        Returns:
            list: A list of email dictionaries.
        """
        try:
            response = self.service.users().messages().list(userId="me", q=query).execute()
            messages: list[dict[str, str]] = response.get("messages", [])
            if not messages:
                log.warning("No emails found.")
                return []
            else:
                log.warning(f"Found {len(messages)} email(s).")
                return messages
        except Exception:
            log.exception("An error occurred while listing emails")
            return []
