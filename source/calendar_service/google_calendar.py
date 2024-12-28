import base64
import json
from datetime import datetime
from pathlib import Path
from typing import Callable

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build
from typing_extensions import override

from .model import Event

# Scopes required for the Calendar API (read/write)
SCOPES = ["https://www.googleapis.com/auth/calendar"]
JsonableType = str | int | float | bool | None | dict[str, "JsonableType"] | list["JsonableType"]


class GoogleCalendarBase:
    """
    Abstract base class for Google Calendar services.
    """

    def __init__(self) -> None:
        self.service: Resource = self.authenticate()

    def authenticate(self) -> Resource:
        """
        Abstract method to authenticate and initialize the Google Calendar service.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement the authenticate method.")

    def create_calendar(self, calendar_name: str) -> str:
        """
        Creates a new Google Calendar.

        Args:
            calendar_name (str): The name of the calendar to create.

        Returns:
            str: The ID of the newly created calendar.
        """
        calendar = {"summary": calendar_name, "timeZone": "UTC"}
        created_calendar = self.service.calendars().insert(body=calendar).execute()
        print(f"Calendar created: {created_calendar['id']}")
        return created_calendar["id"]

    def share_calendar(self, calendar_id: str, email: str, role: str = "reader") -> None:
        """
        Shares the specified calendar with a given email address.

        Args:
            calendar_id (str): The ID of the calendar to share.
            email (str): The email address with which to share the calendar.
            role (str): The role assigned to the email address ('reader', 'writer', 'owner').
        """
        rule = {
            "role": role,
            "scope": {
                "type": "user",
                "value": email,
            },
        }

        try:
            self.service.acl().insert(calendarId=calendar_id, body=rule).execute()
            print(f"Shared calendar {calendar_id} with {email} as {role}.")
        except Exception as e:
            print(f"An error occurred while sharing the calendar: {e}")

    def add_event(self, calendar_id: str, event: Event) -> Event:
        """
        Adds an event to a specific calendar.

        Args:
            calendar_id (str): The ID of the calendar where the event should be added.
            event (Event): The event object from your .model file.

        Returns:
            Event: The created event details.
        """
        created_event = self.service.events().insert(calendarId=calendar_id, body=event).execute()
        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event

    def read_appointments(self, calendar_id: str, time_min: datetime, time_max: datetime) -> list[Event]:
        """
        Reads existing appointments from a specific calendar within a time range.

        Args:
            calendar_id (str): The ID of the calendar to read events from.
            time_min (datetime): The start of the time range as a datetime object.
            time_max (datetime): The end of the time range as a datetime object.

        Returns:
            list[Event]: A list of events within the specified time range.
        """
        assert time_min.tzinfo is not None
        assert time_max.tzinfo is not None

        events_result = (
            self.service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min.isoformat(),
                timeMax=time_max.isoformat(),
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = events_result.get("items", [])
        if not events:
            print("No events found.")
        else:
            print(f"Found {len(events)} event(s).")
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                print(f"Event: {event['summary']} | Start: {start}")
        return events

    def get_calendar_ids(self) -> list[dict[str, str]]:
        """
        Retrieves and prints all calendar IDs associated with the authenticated account.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing calendar summaries and their IDs.
        """
        calendar_list = self.service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])

        if not calendars:
            print("No calendars found.")
            return []

        print("Available calendars:")
        calendar_info: list[dict[str, str]] = []
        for calendar in calendars:
            summary = calendar.get("summary", "No Title")
            calendar_id = calendar.get("id")
            print(f"Name: {summary} | ID: {calendar_id}")
            calendar_info.append({"summary": summary, "id": calendar_id})

        return calendar_info

    def delete_all_events(self, calendar_id: str) -> None:
        """
        Deletes all events from a specified calendar.

        Args:
            calendar_id (str): The ID of the calendar from which to delete all events.
        """
        page_token = None
        while True:
            events_result = (
                self.service.events()
                .list(
                    calendarId=calendar_id,
                    pageToken=page_token,
                    singleEvents=True,
                    orderBy="startTime",
                )
                .execute()
            )

            events = events_result.get("items", [])
            if not events:
                print("No more events found to delete.")
                break

            for event in events:
                try:
                    self.service.events().delete(calendarId=calendar_id, eventId=event["id"]).execute()
                    print(f"Deleted event: {event.get('summary', 'No Title')} | ID: {event['id']}")
                except Exception as e:
                    print(f"An error occurred while deleting event {event['id']}: {e}")

            page_token = events_result.get("nextPageToken")
            if not page_token:
                break


class GoogleCalendarOAuth2(GoogleCalendarBase):
    def __init__(
        self,
        client_secret: str | None = None,  # Accepting client_secret as a string
        token: str | None = None,  # Accepting token as a string
        client_secret_path: Path | str | None = None,  # Optional: Keep for backward compatibility
        token_path: Path | str = "token.json",  # Optional: Keep for backward compatibility
        refresh_callback: Callable[[str, JsonableType], None] | None = None,
        credentials: Credentials | None = None,
    ) -> None:
        """
        Initialize the GoogleCalendarOAuth2 instance by authenticating the user via OAuth2.

        Args:
            client_secret (str | None): The OAuth2 client secrets in JSON format as a string.
            token (str | None): The token JSON in string format for storing user tokens.
            client_secret_path (Path | str | None): Path to the OAuth2 client secrets JSON file (optional).
            token_path (Path | str): Path to the token JSON file (optional).
            credentials (Credentials | None): Existing credentials (optional).
        """
        self.client_secret: str | None = client_secret
        self.token: str | None = token
        self.client_secret_path: Path | None = Path(client_secret_path) if client_secret_path else None
        self.token_path: Path = Path(token_path)
        self.refresh_callback: Callable[[str, JsonableType], None] | None = refresh_callback
        self.credentials: Credentials | None = credentials
        super().__init__()

    @override
    def authenticate(self) -> Resource:
        """
        Authenticates the user using OAuth2 and returns a calendar service object.

        Returns:
            Resource: The authenticated Google Calendar API service object.
        """
        creds = None

        # Load existing tokens if available
        if self.token and self.token.strip():
            creds = Credentials.from_authorized_user_info(json.loads(self.token), SCOPES)
        elif self.token_path.exists():
            with self.token_path.open("r") as token_file:
                creds = Credentials.from_authorized_user_info(json.load(token_file), SCOPES)

        # If there are no valid credentials, perform the OAuth2 flow
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    print(f"Failed to refresh token: {e}")
            else:
                try:
                    if self.client_secret and self.client_secret.strip():
                        client_secrets = json.loads(self.client_secret)
                        flow = InstalledAppFlow.from_client_config(client_secrets, SCOPES)
                    elif self.client_secret_path:
                        flow = InstalledAppFlow.from_client_secrets_file(str(self.client_secret_path), SCOPES)
                    else:
                        raise ValueError("Either 'client_secret' or 'client_secret_path' must be provided.")

                    creds = flow.run_local_server(port=8080)
                except Exception as e:
                    print(f"Failed to create flow: {e}")
                    raise e

            # Save the credentials for the next run if a token path is defined
            if self.token_path:
                creds_json = creds.to_json()
                if self.refresh_callback is not None and creds_json != self.token:
                    self.refresh_callback("token", json.loads(creds_json))
                with self.token_path.open("w") as token_file:
                    _ = token_file.write(creds_json)

        # Build the Google Calendar service
        service = build("calendar", "v3", credentials=creds)
        return service


class GoogleCalendarServiceAccount(GoogleCalendarBase):
    def __init__(
        self,
        service_account_path: Path | str | None = None,
        service_account_base64: str | None = None,
    ) -> None:
        """
        Initialize the GoogleCalendarServiceAccount instance by authenticating the service account.

        Args:
            service_account_path (Path | str | None): Path to the service account JSON key file.
            service_account_base64 (str | None): Base64 encoded service account JSON key.
        """
        self.service_account_path: Path | None = Path(service_account_path) if service_account_path else None
        self.service_account_base64: str | None = service_account_base64
        super().__init__()

    @override
    def authenticate(self) -> Resource:
        """
        Authenticates using a service account JSON key file and returns a calendar service object.

        Returns:
            Resource: The authenticated Google Calendar API service object.
        """
        if self.service_account_path:
            with self.service_account_path.open("r") as f:
                creds_info = json.load(f)
        elif self.service_account_base64:
            decoded = base64.b64decode(self.service_account_base64)
            creds_info = json.loads(decoded)
        else:
            raise ValueError("Either 'service_account_path' or 'service_account_base64' must be provided.")

        creds = service_account.Credentials.from_service_account_info(creds_info, scopes=SCOPES)
        service = build("calendar", "v3", credentials=creds)
        return service
