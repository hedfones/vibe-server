from typing import Literal, NotRequired, TypedDict


class Timestamp(TypedDict):
    dateTime: str
    timeZone: str


class Attendee(TypedDict):
    email: str


class ReminderOverride(TypedDict):
    method: Literal["email", "popup"]
    minutes: int


class Reminder(TypedDict):
    useDefault: bool
    overrides: list[ReminderOverride]


class Event(TypedDict):
    id: NotRequired[str]
    summary: str
    description: NotRequired[str]
    start: Timestamp
    end: Timestamp
    location: str
    attendees: NotRequired[list[Attendee]]
    reminders: Reminder
