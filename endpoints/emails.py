import json
import os
import re
from typing import Literal

import requests
import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from langchain_core.messages import HumanMessage

from source.bedrock_assistant import BedrockAssistant
from source.database import Message
from source.database.model import AssistantFilter, Business
from source.google_service.model import EmailMessage
from source.utils import db, get_email_by_business_id, strip_markdown_lines

log = structlog.stdlib.get_logger()
router = APIRouter()


def api_key_dependency(x_api_key: str = Header(...)):
    if not db.validate_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")


@router.post("/process-unread-emails/", dependencies=[Depends(api_key_dependency)])
def process_unread_emails(x_api_key: str = Header(...)) -> dict[str, int]:
    """
    Process unread emails for a business and send the generated responses.
    """
    business: Business = db.get_business_by_api_key(x_api_key)
    processed_count = process_all_unread_emails_in_business_inbox(business, action="send")
    return {"processed_emails": processed_count}


@router.post("/process-unread-emails-draft/", dependencies=[Depends(api_key_dependency)])
def process_unread_emails_draft(x_api_key: str = Header(...)) -> dict[str, int]:
    """
    Process unread emails for a business and create draft responses.
    """
    business: Business = db.get_business_by_api_key(x_api_key)
    drafts_created_count = process_all_unread_emails_in_business_inbox(business, action="draft")
    return {"drafts_created": drafts_created_count}


def detect_is_customer_email(
    filters: list[AssistantFilter], email: EmailMessage, do_sophisticated_check: bool = True
) -> bool:
    for filter in filters:
        pattern = re.escape(filter.filter_value)
        match_found = re.search(pattern, email["sender"]) is not None
        if match_found and filter.is_blacklist:
            return True
        if match_found and filter.is_blacklist:
            return False

    if not do_sophisticated_check:
        return True

    response = requests.post(
        os.environ["EMAIL_CLASSIFICATION_URL"],
        json={"email": {"sender": email["sender"], "subject": email["subject"], "body": email["body"]}},
    )
    response.raise_for_status()

    response_body: dict[str, str] = response.json()

    return response_body["classification"] == "customer"


def detect_thread_is_actionable(filters: list[AssistantFilter], thread: list[EmailMessage]) -> bool:
    if len(thread) == 1:
        return detect_is_customer_email(filters, thread[0])

    return True


def process_all_unread_emails_in_business_inbox(business: Business, action: Literal["draft", "send"]) -> int:
    """
    Helper function to process unread emails from a business mailbox.
    Generates AI responses via the Assistant and either sends or drafts the email.
    """
    # Initialize the Gmail service using business credentials.
    mailbox = get_email_by_business_id(business.id)

    # Get unread emails.
    query = "is:unread in:inbox"
    if addr := business.inbox_email_address:
        query = f"{query.strip()} to:{addr}"
    unread_emails = mailbox.list_emails(query=query)

    # Configure the BedrockAssistant for email responses.
    asst_config = db.get_assistant_by_business_and_type(business.id, "email")
    if not asst_config:
        return 0
    tz = db.get_first_associate_timezone_by_business_id(business.id)

    count = 0
    thread_ids = {m["threadId"] for m in unread_emails}
    for thread_id in thread_ids:
        # Get full email thread.
        thread = mailbox.get_messages_in_thread(thread_id)
        if not thread:
            continue
        # if not detect_thread_is_actionable(asst_config.filters, thread):
        #     continue

        with BedrockAssistant.from_postgres(asst_config, client_timezone=tz) as assistant:
            # Initialize with AWS Bedrock
            conversation = db.create_conversation(asst_config.id, tz, assistant.thread_id)
            messages: list[Message] = []
            for email in thread:
                message = {"role": "user", "content": json.dumps(email)}
                assistant.add_message(message)
                messages.append(Message(**message, conversation_id=conversation.id))
            response = assistant.retrieve_response([HumanMessage(msg.content) for msg in messages])
        messages.append(Message(conversation_id=conversation.id, role="assistant", content=response))
        db.insert_messages(messages)

        message_id = thread[-1]["message_id"]
        response_payload: dict[str, str] = json.loads(strip_markdown_lines(response))

        if action == "send":
            # Send the email.
            mailbox.send_email(
                to=response_payload["to"],
                subject=response_payload["subject"],
                body=response_payload["body"],
                message_id=message_id,
                thread_id=thread_id,
                is_html=True,
            )
        elif action == "draft":
            # Create a draft.
            mailbox.create_draft(
                to=response_payload["to"],
                subject=response_payload["subject"],
                body=response_payload["body"],
                message_id=message_id,
                thread_id=thread_id,
                is_html=True,
            )
        else:
            raise ValueError(f"Unknown action: {action}")

        mailbox.mark_thread_as_read(thread_id)
        count += 1

    return count
