import os.path
import pickle
from datetime import date, datetime

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

# Scopes required for the Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendar:
    def __init__(self) -> None:
        self.service: Resource = self.authenticate()

    # Authenticate and build the service
    def authenticate(self) -> Resource:
        """
        Authenticates the user with Google Calendar and returns a service object.

        Setup: Enable the Google Calendar API
            Go to the Google Cloud Console.
            Create a new project or select an existing one.
            Enable the Google Calendar API:
                Navigate to APIs & Services > Library.
                Search for Google Calendar API and enable it.
            Configure the API credentials:
                Go to APIs & Services > Credentials.
                Click Create Credentials and choose OAuth 2.0 Client IDs.
                Set the application type to Desktop App or Web App depending on your needs.
                Download the credentials.json file.

        Returns:
            Resource: The authenticated Google Calendar API service object.
        """
        creds = None
        if os.path.exists("token.pickle"):
            with open("token.pickle", "rb") as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    "credentials.json", SCOPES
                )
                creds = flow.run_local_server(port=0)
            with open("token.pickle", "wb") as token:
                pickle.dump(creds, token)
        return build("calendar", "v3", credentials=creds)

    # 1. Create a new calendar
    def create_calendar(self, calendar_name: str) -> str:
        """
        Creates a new Google Calendar.

        Args:
            service (Resource): The authenticated Google Calendar API service object.
            calendar_name (str): The name of the calendar to create.

        Returns:
            str: The ID of the newly created calendar.
        """
        calendar: dict[str, str] = {"summary": calendar_name, "timeZone": "UTC"}
        created_calendar = self.service.calendars().insert(body=calendar).execute()
        print(f"Calendar created: {created_calendar['id']}")
        return created_calendar["id"]

    # 2. Add an event to a specific calendar
    def add_event(
        self, calendar_id: str, event: dict[str, str | int | date | datetime]
    ) -> dict[str, str | int | date | datetime]:
        """
        Adds an event to a specific calendar.

        Args:
            service (Resource): The authenticated Google Calendar API service object.
            calendar_id (str): The ID of the calendar where the event should be added.
            event (Dict[str, Any]): The event details as a dictionary.

        Returns:
            Dict[str, Any]: The created event details.
        """
        created_event = (
            self.service.events().insert(calendarId=calendar_id, body=event).execute()
        )
        print(f"Event created: {created_event.get('htmlLink')}")
        return created_event
