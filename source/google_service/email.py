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

    def read_email(self, email_id: str) -> dict:
        """
        Reads an email's full content by its ID.

        Args:
            email_id (str): The ID of the email to read.

        Returns:
            dict: A dictionary containing the email information, including the subject and body.
        """
        try:
            # Retrieve the full email message
            message = self.service.users().messages().get(userId="me", id=email_id, format="full").execute()
            email_data = message.get("payload", {}).get("parts", [])

            # Decode the email body
            if email_data:
                # For simplicity, we will extract the first part
                part = email_data[0]
                body = part.get("body", {}).get("data", "")
                # Decode the base64url encoded email body
                decoded_body = urlsafe_b64encode(body).decode()

                # Find the subject
                headers = message.get("payload", {}).get("headers", [])
                subject = next((header["value"] for header in headers if header["name"] == "Subject"), None)

                # Return the email details
                return {"subject": subject, "body": decoded_body}
            else:
                log.warning(f"No parts found in email with ID: {email_id}")
                return {}
        except Exception:
            log.exception(f"An error occurred while reading the email with ID: {email_id}")
            return {}
