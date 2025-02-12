from base64 import urlsafe_b64decode, urlsafe_b64encode
from email.mime.text import MIMEText
from typing import Any

import markdown
import structlog

from .auth import GoogleServiceBase
from .model import EmailHeader, EmailListItem, EmailMessage, EmailMesssagePayload

log = structlog.stdlib.get_logger()


class GoogleGmail(GoogleServiceBase["GoogleGmail"]):
    api_name: str = "gmail"
    api_version: str = "v1"

    def create_email_message(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = False,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> EmailMesssagePayload:
        if not is_html:
            body = markdown.markdown(body)

        message = MIMEText(body, "html")
        message["to"] = to
        message["subject"] = subject
        if message_id:
            message["In-Reply-To"] = message_id
            message["References"] = message_id
        else:
            message["References"] = ""

        raw_message = urlsafe_b64encode(message.as_bytes()).decode()

        body_payload: EmailMesssagePayload = {"raw": raw_message}
        if thread_id:
            body_payload["threadId"] = thread_id

        return body_payload

    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = False,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        """
        Sends an email via Gmail.

        Args:
            to (str): Recipient email address.
            subject (str): Subject of the email.
            body (str): Body of the email, can be markdown or HTML.
            is_html (bool): True if the body is HTML, False if it is plain text or markdown.
            thread_id (str): The ID of the thread to which this email is a reply.
        """
        message = self.create_email_message(to, subject, body, is_html, message_id, thread_id)
        try:
            self.service.users().messages().send(userId="me", body=message).execute()
            log.info(f"Email sent to {to} in thread {thread_id}")
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
                log.info(f"Found {len(messages)} email(s).")
                return messages
        except Exception:
            log.exception("An error occurred while listing emails")
            return []

    def _parse_email_message(self, message: dict[str, Any]) -> EmailMessage | None:
        """
        Parses an email message to extract the sender, subject, body, and date.

        Args:
            message: The message object from Gmail API response.

        Returns:
            dict: A dictionary containing the email information, including the sender, subject, body, and date.
        """
        email_data = message.get("payload", {}).get("parts", [])
        if email_data:
            # For simplicity, we will extract the first part
            part = email_data[0]
            body = part.get("body", {}).get("data", "")
            # Decode the base64url encoded email body
            decoded_body = urlsafe_b64decode(body.encode("utf-8")).decode("utf-8")

            # Find the subject, sender, and date
            headers: list[EmailHeader] = message.get("payload", {}).get("headers", [])
            subject = next((header["value"] for header in headers if header["name"] == "Subject"))
            sender = next((header["value"] for header in headers if header["name"] == "From"))
            date_sent = next((header["value"] for header in headers if header["name"] == "Date"))
            message_id = next((header["value"] for header in headers if header["name"] == "Message-ID"))

            # Return the email details including Message-ID
            message_details: EmailMessage = {
                "sender": sender,
                "subject": subject,
                "body": decoded_body,
                "date_sent": date_sent,
                "message_id": message_id,
            }
            return message_details
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

    def mark_thread_as_read(self, thread_id: str) -> None:
        """
        Marks all messages in a given thread as read.

        Args:
            thread_id (str): The ID of the thread to mark as read.
        """
        try:
            # Retrieve the thread's messages
            thread = self.service.users().threads().get(userId="me", id=thread_id).execute()
            messages = thread.get("messages", [])

            # Prepare the request body to remove the "UNREAD" label
            for message in messages:
                message_id = message["id"]
                self.service.users().messages().modify(
                    userId="me", id=message_id, body={"removeLabelIds": ["UNREAD"]}
                ).execute()

            log.info(f"All messages in thread {thread_id} marked as read.")
        except Exception:
            log.exception(f"An error occurred while marking thread {thread_id} as read.")

    def create_draft(
        self,
        to: str,
        subject: str,
        body: str,
        is_html: bool = False,
        message_id: str | None = None,
        thread_id: str | None = None,
    ) -> None:
        message = self.create_email_message(to, subject, body, is_html, message_id, thread_id)
        payload = {"message": message}
        try:
            # Log the constructed message for debugging
            log.debug("Creating draft with message:", message=message)
            draft = self.service.users().drafts().create(userId="me", body=payload).execute()
            log.info(f"Draft created for {to} in thread {thread_id}, draft ID: {draft['id']}")
        except Exception as e:
            log.exception("An error occurred while creating the draft.")
            raise RuntimeError("Failed to create email draft.") from e  # Optionally re-raise with a custom message
