import json
from datetime import datetime

import pytz
from pydantic import BaseModel
from typing_extensions import override

from .calendar import Event
from .database import Message
from .notion import NotionPage


class ConversationInitRequest(BaseModel):
    """Request model for initializing a conversation.

    Attributes:
        business_id (int): The ID of the business initiating the conversation.
    """

    business_id: int
    client_timezone: str


class ConversationInitResponse(BaseModel):
    """Response model for a conversation initialization request.

    Attributes:
        conversation_id (int): The unique ID assigned to the initialized conversation.
    """

    conversation_id: int
    message: Message


class UserMessageRequest(BaseModel):
    conversation_id: int
    content: str


class UserMessageResponse(BaseModel):
    message: Message


class AvailabilityWindow(BaseModel):
    start_time: datetime
    end_time: datetime
    associate_id: int | None = None

    @property
    def duration_minutes(self) -> float:
        timedelta = self.end_time - self.start_time
        return abs(timedelta.total_seconds()) // 60

    @override
    def __str__(self) -> str:
        return (
            "Availability Window:\n"
            + f"\tDate: {self.start_time.strftime('%A, %B %d, %Y')}\n"
            + f"\tStart Time: {self.start_time.strftime('%I:%M:%S %p %Z')}\n"
            + f"\tEnd Time: {self.end_time.strftime('%I:%M:%S %p %Z')}\n"
            + f"\tAssociate ID: {self.associate_id}"
        )

    def localize(self, timezone: str) -> None:
        tz = pytz.timezone(timezone)
        self.start_time = self.start_time.astimezone(tz)
        self.end_time = self.end_time.astimezone(tz)


class CheckAvailabilityRequest(BaseModel):
    product_id: int
    location_id: int


class GetProductLocationsRequest(BaseModel):
    product_id: int


class SetAppointmentsRequest(BaseModel):
    location_id: int
    associate_id: int
    start_datetime: datetime
    end_datetime: datetime
    summary: str
    attendee_emails: list[str]
    description: str = ""

    @classmethod
    def parse_json_to_request(cls, json_str: str) -> "SetAppointmentsRequest":
        # Parse the JSON string
        data = json.loads(json_str)

        # Convert string date and time to appropriate types
        data["start_datetime"] = start = datetime.fromisoformat(data["start_datetime"])
        data["end_datetime"] = end = datetime.fromisoformat(data["end_datetime"])  # Same for end time
        assert start.tzinfo is not None, "Start datetime must be timezone-aware."
        assert end.tzinfo is not None, "End datetime must be timezone-aware."

        # Create the SetAppointmentsRequest object
        request = SetAppointmentsRequest(**data)

        return request


class GetProductPhotosRequest(BaseModel):
    product_id: int


class GetPhotoRequest(BaseModel):
    photo_id: int


class Appointment(BaseModel):
    start: datetime
    end: datetime

    @classmethod
    def from_event(cls, event: Event) -> "Appointment":
        event_start = event["start"]
        dt = datetime.fromisoformat(event_start["dateTime"])
        if not dt.tzinfo:
            tz = pytz.timezone(event_start["timeZone"])
            event_start_dtz = tz.localize(dt)
        else:
            event_start_dtz = dt

        event_end = event["end"]
        dt = datetime.fromisoformat(event_end["dateTime"])
        if not dt.tzinfo:
            tz = pytz.timezone(event_end["timeZone"])
            event_end_dtz = tz.localize(dt)
        else:
            event_end_dtz = dt

        return cls(start=event_start_dtz, end=event_end_dtz)


class SyncNotionRequest(BaseModel):
    business_id: int


class SyncNotionResponse(BaseModel):
    """Response model for syncing Notion content."""

    markdown_content: NotionPage


class UpdateAssistantRequest(BaseModel):
    business_id: int
