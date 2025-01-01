from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.mime.text import MIMEText
from typing import Any

import markdown
import structlog

from .auth import GoogleServiceBase
from .model import EmailListItem, EmailMessage

log = structlog.stdlib.get_logger()


class GoogleGmail(GoogleServiceBase["GoogleGmail"]):
    api_name: str = "gmail"
    api_version: str = "v1"

    def send_email(self, to: str, subject: str, body: str, is_html: bool = False) -> None:
        """
        Sends an email via Gmail.

        Args:
            to (str): Recipient email address.
            subject (str): Subject of the email.
            body (str): Body of the email, can be markdown or HTML.
            is_html (bool): True if the body is HTML, False if it is plain text or markdown.
        """
        if not is_html:
            # If it's markdown, convert it to HTML
            body = markdown.markdown(body)

        message = MIMEText(body, "html")
        message["to"] = to
        message["subject"] = subject
        raw_message = urlsafe_b64encode(message.as_bytes()).decode()

        try:
            self.service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
            log.info(f"Email sent to {to}")
        except Exception:
            log.exception("An error occurred while sending the email.")

    def list_emails(self, query: str = "") -> list[EmailListItem]:
        """
        Lists emails in the user's Gmail inbox.

        Args:
            query (str): String used to filter the emails using Gmail API. (e.g., 'is:unread')

        Returns:
            list: A list of email dictionaries.
        """
        try:
            response = self.service.users().messages().list(userId="me", q=query).execute()
            messages: list[EmailListItem] = response.get("messages", [])
            if not messages:
                log.warning("No emails found.")
                return []
            else:
                log.warning(f"Found {len(messages)} email(s).")
                return messages
        except Exception:
            log.exception("An error occurred while listing emails")
            return []

    def _parse_email_message(self, message: dict[str, Any]) -> EmailMessage | None:
        """
        Parses an email message to extract the sender, subject, and body.

        Args:
            message: The message object from Gmail API response.

        Returns:
            dict: A dictionary containing the email information, including the sender, subject, and body.
        """
        email_data = message.get("payload", {}).get("parts", [])
        if email_data:
            # For simplicity, we will extract the first part
            part = email_data[0]
            body = part.get("body", {}).get("data", "")
            # Decode the base64url encoded email body
            decoded_body = urlsafe_b64decode(body.encode("utf-8")).decode("utf-8")

            # Find the subject and the sender
            headers = message.get("payload", {}).get("headers", [])
            subject = next((header["value"] for header in headers if header["name"] == "Subject"), None)
            sender = next((header["value"] for header in headers if header["name"] == "From"), None)

            # Return the email details
            return {"sender": sender, "subject": subject, "body": decoded_body}
        else:
            log.warning(f"No parts found in message with ID: {message.get('id')}")
            return None

    def read_email(self, email_id: str) -> EmailMessage | None:
        """
        Reads an email's full content by its ID.

        Args:
            email_id (str): The ID of the email to read.

        Returns:
            dict: A dictionary containing the email information, including the sender, subject, and body.
        """
        try:
            message = self.service.users().messages().get(userId="me", id=email_id, format="full").execute()
            return self._parse_email_message(message)
        except Exception:
            log.exception(f"An error occurred while reading the email with ID: {email_id}")
            return None

    def get_messages_in_thread(self, thread_id: str) -> list[EmailMessage]:
        """
        Retrieves all messages in a given thread.

        Args:
            thread_id (str): The ID of the thread to retrieve messages from.

        Returns:
            list: A list of email dictionaries in the thread.
        """
        try:
            thread = self.service.users().threads().get(userId="me", id=thread_id).execute()
            messages = thread.get("messages", [])

            email_messages = []
            for message in messages:
                parsed_message = self._parse_email_message(message)
                if parsed_message:
                    email_messages.append(parsed_message)

            return email_messages

        except Exception:
            log.exception(f"An error occurred while retrieving messages in the thread with ID: {thread_id}")
            return []
