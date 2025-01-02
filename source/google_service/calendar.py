from datetime import datetime

from .auth import GoogleServiceBase
from .model import Event


# Scopes required for the Calendar API (read/write)
class GoogleCalendar(GoogleServiceBase["GoogleCalendar"]):
    api_name: str = "calendar"
    api_version: str = "v3"

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
