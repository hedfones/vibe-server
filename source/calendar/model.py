from typing import Literal, TypedDict


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
    summary: str
    description: str
    start: Timestamp
    end: Timestamp
    location: str
    attendees: list[Attendee]
    reminders: Reminder
