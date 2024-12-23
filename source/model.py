import json
from datetime import datetime

import pytz
from pydantic import BaseModel
from typing_extensions import override

from .calendar_service import Event
from .database import Message
from .notion import NotionPage


class ConversationInitRequest(BaseModel):
    """Request model for initializing a conversation.

    Attributes:
        business_id (int): The ID of the business initiating the conversation.
        client_timezone (str): The timezone of the client.
    """

    business_id: int
    client_timezone: str


class ConversationInitResponse(BaseModel):
    """Response model for a conversation initialization request.

    Attributes:
        conversation_id (int): The unique ID assigned to the initialized conversation.
        message (Message): The message object related to the conversation.
    """

    conversation_id: int
    message: Message


class UserMessageRequest(BaseModel):
    """Request model for sending a user message.

    Attributes:
        conversation_id (int): The ID of the conversation to which the message belongs.
        content (str): The content of the user's message.
    """

    conversation_id: int
    content: str


class UserMessageResponse(BaseModel):
    """Response model for a user message.

    Attributes:
        message (Message): The message object sent by the user.
    """

    message: Message


class AvailabilityWindow(BaseModel):
    """Model representing an availability window.

    Attributes:
        start_time (datetime): The start time of the availability.
        end_time (datetime): The end time of the availability.
        associate_id (Optional[int]): The ID of the associated person, if any.
    """

    start_time: datetime
    end_time: datetime
    associate_id: int | None = None

    @property
    def duration_minutes(self) -> float:
        """Calculate the duration of the availability window in minutes."""
        timedelta = self.end_time - self.start_time
        return abs(timedelta.total_seconds()) // 60

    @override
    def __str__(self) -> str:
        """Return a string representation of the availability window."""
        return (
            "Availability Window:\n"
            + f"\tDate: {self.start_time.strftime('%A, %B %d, %Y')}\n"
            + f"\tStart Time: {self.start_time.strftime('%I:%M:%S %p %Z')}\n"
            + f"\tEnd Time: {self.end_time.strftime('%I:%M:%S %p %Z')}\n"
            + f"\tAssociate ID: {self.associate_id}"
        )

    def localize(self, timezone: str) -> None:
        """Localize the start and end times to the specified timezone.

        Args:
            timezone (str): The timezone to which the start and end times should be converted.
        """
        tz = pytz.timezone(timezone)
        self.start_time = self.start_time.astimezone(tz)
        self.end_time = self.end_time.astimezone(tz)


class CheckAvailabilityRequest(BaseModel):
    """Request model for checking availability.

    Attributes:
        product_id (int): The ID of the product.
        location_id (int): The ID of the location.
    """

    product_id: int
    location_id: int


class GetProductLocationsRequest(BaseModel):
    """Request model for getting product locations.

    Attributes:
        product_id (int): The ID of the product.
    """

    product_id: int


class SetAppointmentsRequest(BaseModel):
    """Request model for setting an appointment.

    Attributes:
        location_id (int): The ID of the location.
        associate_id (int): The ID of the associate.
        start_datetime (datetime): The start date and time of the appointment.
        end_datetime (datetime): The end date and time of the appointment.
        summary (str): A summary of the appointment.
        attendee_emails (List[str]): List of attendee email addresses.
        description (str): A description of the appointment.
    """

    location_id: int
    associate_id: int
    start_datetime: datetime
    end_datetime: datetime
    summary: str
    attendee_emails: list[str]
    description: str = ""

    @classmethod
    def parse_json_to_request(cls, json_str: str) -> "SetAppointmentsRequest":
        """Parse a JSON string to create a SetAppointmentsRequest object.

        Args:
            json_str (str): The JSON string to parse.

        Returns:
            SetAppointmentsRequest: The constructed request object.

        Raises:
            AssertionError: If start_datetime or end_datetime are not timezone-aware.
        """
        # Parse the JSON string
        data = json.loads(json_str)

        # Convert string date and time to appropriate types and ensure they are timezone-aware
        data["start_datetime"] = start = datetime.fromisoformat(data["start_datetime"])
        data["end_datetime"] = end = datetime.fromisoformat(data["end_datetime"])
        assert start.tzinfo is not None, "Start datetime must be timezone-aware."
        assert end.tzinfo is not None, "End datetime must be timezone-aware."

        # Create the SetAppointmentsRequest object
        request = SetAppointmentsRequest(**data)

        return request


class GetProductPhotosRequest(BaseModel):
    """Request model for getting product photos.

    Attributes:
        product_id (int): The ID of the product.
    """

    product_id: int


class GetPhotoRequest(BaseModel):
    """Request model for getting a photo.

    Attributes:
        photo_id (int): The ID of the photo.
    """

    photo_id: int


class Appointment(BaseModel):
    """Model representing an appointment.

    Attributes:
        start (datetime): The start time of the appointment.
        end (datetime): The end time of the appointment.
    """

    start: datetime
    end: datetime

    @classmethod
    def from_event(cls, event: Event) -> "Appointment":
        """Create an Appointment object from an Event.

        Args:
            event (Event): The event from which the appointment is created.

        Returns:
            Appointment: The constructed appointment object.
        """
        # Extract start time from the event and ensure it is timezone-aware
        event_start = event["start"]
        dt = datetime.fromisoformat(event_start["dateTime"])
        if not dt.tzinfo:
            tz = pytz.timezone(event_start["timeZone"])
            event_start_dtz = tz.localize(dt)
        else:
            event_start_dtz = dt

        # Extract end time from the event and ensure it is timezone-aware
        event_end = event["end"]
        dt = datetime.fromisoformat(event_end["dateTime"])
        if not dt.tzinfo:
            tz = pytz.timezone(event_end["timeZone"])
            event_end_dtz = tz.localize(dt)
        else:
            event_end_dtz = dt

        return cls(start=event_start_dtz, end=event_end_dtz)


class SyncNotionRequest(BaseModel):
    """Request model for syncing Notion content.

    Attributes:
        business_id (int): The ID of the business.
    """

    business_id: int


class SyncNotionResponse(BaseModel):
    """Response model for syncing Notion content.

    Attributes:
        markdown_content (NotionPage): The markdown content from Notion.
    """

    markdown_content: NotionPage


class UpdateAssistantRequest(BaseModel):
    """Request model for updating an assistant.

    Attributes:
        business_id (int): The ID of the business.
    """

    business_id: int
