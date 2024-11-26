import pickle
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build

from .model import Event

# Scopes required for the Calendar API
SCOPES = ["https://www.googleapis.com/auth/calendar"]


class GoogleCalendar:
    def __init__(
        self,
        token_path: Path | str = "token.pickle",
        credentials_path: Path | str = "credentials.json",
    ) -> None:
        self.token_path: Path = Path(token_path)
        self.credentials_path: Path = Path(credentials_path)
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
        if self.token_path.exists():
            with self.token_path.open("rb") as token:
                creds = pickle.load(token)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=63103)
            with self.token_path.open("wb") as token:
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
    def add_event(self, calendar_id: str, event: Event) -> Event:
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

    def read_appointments(
        self, calendar_id: str, time_min: str, time_max: str
    ) -> list[Event]:
        """
        Reads existing appointments from a specific calendar within a time range.

        Args:
            service (Resource): The authenticated Google Calendar API service object.
            calendar_id (str): The ID of the calendar to read events from.
            time_min (str): The start of the time range in ISO 8601 format (e.g., "2024-11-25T00:00:00Z").
            time_max (str): The end of the time range in ISO 8601 format (e.g., "2024-11-30T23:59:59Z").

        Returns:
            List[Dict[str, Any]]: A list of event details within the specified time range.
        """
        events_result = (
            self.service.events()
            .list(
                calendarId=calendar_id,
                timeMin=time_min,
                timeMax=time_max,
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

        Args:
            service (Resource): The authenticated Google Calendar API service object.

        Returns:
            List[Dict[str, str]]: A list of dictionaries containing calendar summaries and their IDs.
        """
        # Retrieve the list of calendars
        calendar_list = self.service.calendarList().list().execute()
        calendars = calendar_list.get("items", [])

        if not calendars:
            print("No calendars found.")
            return []

        # Print and return the list of calendar IDs
        print("Available calendars:")
        calendar_info: list[dict[str, str]] = []
        for calendar in calendars:
            summary = calendar.get("summary", "No Title")
            calendar_id = calendar.get("id")
            print(f"Name: {summary} | ID: {calendar_id}")
            calendar_info.append({"summary": summary, "id": calendar_id})

        return calendar_info
