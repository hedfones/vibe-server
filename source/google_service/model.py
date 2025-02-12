from typing import Callable, Literal, NotRequired, TypedDict

JsonableType = str | int | float | bool | None | dict[str, "JsonableType"] | list["JsonableType"]
SecretUpdateCallbackFunctionType = Callable[[str, JsonableType], None]


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


class EmailListItem(TypedDict):
    id: str
    threadId: str


class EmailMessage(TypedDict):
    subject: str
    body: str
    sender: str
    date_sent: str
    message_id: str


class EmailHeader(TypedDict):
    value: str
    name: str


class EmailMesssagePayload(TypedDict):
    raw: str
    threadId: NotRequired[str]
