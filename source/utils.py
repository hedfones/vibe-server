import json

import structlog
from fastapi import HTTPException

from .database import DatabaseService, PostgresCredentials
from .google_service import GoogleCalendar, GoogleGmail, SecretUpdateCallbackFunctionType
from .secret_manager import SecretsManager

log = structlog.stdlib.get_logger()

# Initialize SecretsManager to manage access to sensitive credentials
secrets = SecretsManager()

# Set up database credentials using secrets manager
db_creds = PostgresCredentials(
    user=secrets.get("POSTGRES_USER"),
    password=secrets.get("POSTGRES_PASSWORD"),
    database=secrets.get("POSTGRES_DB"),
    host=secrets.get("POSTGRES_HOST"),
    port=int(secrets.get("POSTGRES_PORT")),
)
db = DatabaseService(db_creds)


def get_google_service_client_credentials(secret_id: str) -> tuple[str, str | None, SecretUpdateCallbackFunctionType]:
    secret_name = f"GOOGLE_OAUTH2_{secret_id}"
    creds = secrets.get_raw(secret_name)
    client_credentials, token = creds["secret"], creds.get("token")
    token = json.dumps(token) if token else None
    client_credentials = json.dumps(client_credentials)
    callback = secrets.get_update_callback(secret_name)
    return client_credentials, token, callback


def get_google_calendar_by_calendar_id(calendar_id: str) -> GoogleCalendar:
    client_secret, token, callback = get_google_service_client_credentials(calendar_id)
    return GoogleCalendar.from_oauth2(client_secret, token, callback)


def get_gmail_by_email_id(email_id: str) -> GoogleGmail:
    client_secret, token, callback = get_google_service_client_credentials(email_id)
    return GoogleGmail.from_oauth2(client_secret, token, callback)


def get_calendar_by_business_id(business_id: int) -> GoogleCalendar:
    """Fetch Google Calendar for a given business ID.

    Args:
        business_id (int): The ID of the business.

    Returns:
        GoogleCalendar: An instance of GoogleCalendar configured with credentials.

    Raises:
        HTTPException: If the business or Google Calendar credentials are not found.
    """
    logger = log.bind(business_id=business_id)
    logger.debug("Fetching calendar by business ID.")
    business = db.get_business_by_id(business_id)
    assert business is not None, f"Business not found for ID `{business_id}`."

    if business.calendar_service == "google":
        logger.debug("Business uses Google Calendar service.")
        return get_google_calendar_by_calendar_id(business.calendar_service_id)
    else:
        logger.error("Unrecognized calendar service.", service=business.calendar_service)
        raise HTTPException(400, detail=f"Unrecognized calendar service `{business.calendar_service}`.")


def get_email_by_business_id(business_id: int) -> GoogleGmail:
    logger = log.bind(business_id=business_id)
    logger.debug("Fetching email by business ID.")
    business = db.get_business_by_id(business_id)
    assert business is not None, f"Business not found for ID `{business_id}`."

    if business.email_service == "google":
        logger.debug("Business uses Google Gmail service.")
        return get_gmail_by_email_id(business.email_service_id)
    else:
        logger.error("Unrecognized email service.", service=business.email_service)
        raise HTTPException(400, detail=f"Unrecognized email service `{business.email_service}`.")


def strip_markdown_lines(text: str):
    # Split the text into lines
    lines = text.splitlines()

    # Check if the first and last lines are markdown indicators
    if lines[0].strip() == "```json":
        lines = lines[1:]
    if lines[-1].strip() == "```":
        lines = lines[:-1]

    # Join the remaining lines
    stripped_text = "\n".join(lines)

    return stripped_text
