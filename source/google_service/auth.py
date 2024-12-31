import base64
import json
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
        token: str | None = None,  # Accepting token as a string
        refresh_callback: Callable[[str, JsonableType], None] | None = None,
    ) -> T:
        creds = None

        # Load existing tokens if available
        if token and token.strip():
            log.debug("REMOVE2", token=token, token_json=json.loads(token))
            assert isinstance(creds, Credentials), "Wrong credential instance returned"

        # If there are no valid credentials, perform the OAuth2 flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                client_secrets = json.loads(client_secret)
                flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)
                creds = flow.run_local_server(port=8081)

                # Check if the refresh_token is available
                if hasattr(creds, "refresh_token"):
                    log.info("Refresh Token obtained: %s", creds.refresh_token)
                else:
                    log.warning("No refresh token obtained, please verify your consent screen settings.")

                # Save the credentials for the next run if a token path is defined
                creds_json = creds.to_json()
                log.info("Credentials JSON: %s", creds_json)
                if refresh_callback is not None and creds_json != token:
                    refresh_callback("token", json.loads(creds_json))

        # Build the Google Calendar service
        service = build(cls.api_name, cls.api_version, credentials=creds)
        return cls(service)

    @classmethod
    def from_service_account(cls: type[T], service_account_base64: str) -> T:
        decoded = base64.b64decode(service_account_base64)
        creds_info = json.loads(decoded)
        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        service = build(cls.api_name, cls.api_version, credentials=creds)
        return cls(service)
