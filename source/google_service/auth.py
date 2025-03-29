import base64
import json
import pickle
from typing import Generic, TypeVar

import structlog
from fastapi import HTTPException
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from googleapiclient.discovery import Resource, build

from .model import SecretUpdateCallbackFunctionType

log = structlog.stdlib.get_logger()

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    # "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


GoogleServiceType = TypeVar("GoogleServiceType", bound="GoogleServiceBase")


class GoogleServiceBase(Generic[GoogleServiceType]):
    """
    Abstract base class for Google Calendar services.
    """

    api_name: str = "NOT_SET"
    api_version: str = "NOT_SET"

    def __init__(self, service: Resource) -> None:
        self.service: Resource = service

    @classmethod
    def from_oauth2(
        cls: type[GoogleServiceType],
        token: str | None,  # Accepting token as a string
        refresh_callback: SecretUpdateCallbackFunctionType,
    ) -> GoogleServiceType:
        if token is None:
            raise HTTPException(400, detail="Organization has not completed Google OAuth2 setup.")

        # Attempt to retrieve the stored token from AWS Secrets Manager
        try:
            token_bytes = base64.b64decode(token)
            creds = pickle.loads(token_bytes)
        except Exception as e:
            log.exception(f"Failed to load credentials from Secrets Manager: {e}")
            raise HTTPException(500, detail="Failed to load google credentials from Secrets Manager.") from e

        # If credentials are not available or invalid, initiate OAuth2 flow
        if not creds.valid:
            if creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    log.info("Credentials refreshed.")
                except Exception as e:
                    log.exception(f"Error refreshing credentials: {e}")
                    creds = None

            # Serialize and store the updated credentials back to Secrets Manager
            try:
                token_pickle = pickle.dumps(creds)
                token_encoded = base64.b64encode(token_pickle).decode("utf-8")
                refresh_callback("token", token_encoded)
            except Exception as e:
                log.exception(f"Failed to save credentials to Secrets Manager: {e}")
                raise

        # Build the Google API service
        service = build(cls.api_name, cls.api_version, credentials=creds)
        return cls(service)

    @classmethod
    def from_service_account(cls: type[GoogleServiceType], service_account_base64: str) -> GoogleServiceType:
        decoded = base64.b64decode(service_account_base64)
        creds_info = json.loads(decoded)
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        service = build(cls.api_name, cls.api_version, credentials=creds)
        return cls(service)
