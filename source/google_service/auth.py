import base64
import json
import pickle
from typing import Callable, Generic, TypeVar

import structlog
from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from .model import JsonableType

log = structlog.stdlib.get_logger()

SCOPES = [
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


T = TypeVar("T", bound="GoogleServiceBase")


class GoogleServiceBase(Generic[T]):
    """
    Abstract base class for Google Calendar services.
    """

    api_name: str = "NOT_SET"
    api_version: str = "NOT_SET"

    def __init__(self, service: Resource) -> None:
        self.service: Resource = service

    @classmethod
    def from_oauth2(
        cls: type[T],
        client_secret: str,  # Accepting client_secret as a string
        token: str | None,  # Accepting token as a string
        refresh_callback: Callable[[str, JsonableType], None],
    ) -> T:
        creds: Credentials | None = None

        # Attempt to retrieve the stored token from AWS Secrets Manager
        try:
            if token:
                token_bytes = base64.b64decode(token)
                creds = pickle.loads(token_bytes)
        except Exception as e:
            log.error(f"Failed to load credentials from Secrets Manager: {e}")

        # If credentials are not available or invalid, initiate OAuth2 flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    log.info("Credentials refreshed.")
                except Exception as e:
                    log.error(f"Error refreshing credentials: {e}")
                    creds = None

            if not creds or not creds.valid:
                try:
                    client_secrets = json.loads(client_secret)
                    flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)
                    creds = flow.run_local_server(port=8081)
                    log.info("Credentials obtained from OAuth flow.")
                except Exception as e:
                    log.error(f"Error during OAuth flow: {e}")
                    raise

            # Serialize and store the updated credentials back to Secrets Manager
            try:
                token_pickle = pickle.dumps(creds)
                token_encoded = base64.b64encode(token_pickle).decode("utf-8")
                refresh_callback("token", token_encoded)
            except Exception as e:
                log.error(f"Failed to save credentials to Secrets Manager: {e}")
                raise

        # Build the Google API service
        service = build(cls.api_name, cls.api_version, credentials=creds)
        return cls(service)

    @classmethod
    def from_service_account(cls: type[T], service_account_base64: str) -> T:
        decoded = base64.b64decode(service_account_base64)
        creds_info = json.loads(decoded)
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        service = build(cls.api_name, cls.api_version, credentials=creds)
        return cls(service)
