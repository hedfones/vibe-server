import uuid
from datetime import datetime
from enum import Enum

import pytz
from sqlalchemy import Column, DateTime, Sequence, func
from sqlmodel import Field, Relationship, SQLModel
from typing_extensions import override

utc = pytz.UTC


class Business(SQLModel, table=True):
    """Represents a business entity with various attributes and relationships."""

    id: int = Field(default=None, primary_key=True)
    name: str
    calendar_service: str
    calendar_service_id: str
    calendar_service_authenticated: bool = False
    email_service: str
    email_service_id: str
    inbox_email_address: str | None = None
    notion_page_id: str
    created_at: datetime = Field(
        # Sets the default creation time to now in UTC if not provided.
        default_factory=lambda: datetime.now(utc),
        # Sets the server's default column value for the creation time.
        sa_column=Column(DateTime, server_default=func.now()),
    )

    # Define relationships to other entities.
    products: list["Product"] = Relationship(back_populates="business")
    associates: list["Associate"] = Relationship(back_populates="business")
    locations: list["Location"] = Relationship(back_populates="business")
    photos: list["Photo"] = Relationship(back_populates="business")
    assistants: list["Assistant"] = Relationship(back_populates="business")
    admins: list["Admin"] = Relationship(back_populates="business")
    api_keys: list["ApiKey"] = Relationship(back_populates="business")


class Admin(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    name: str
    email: str
    created_at: datetime = Field(
        # Sets the default creation time to now in UTC if not provided.
        default_factory=lambda: datetime.now(utc),
        # Sets the server's default column value for the creation time.
        sa_column=Column(DateTime, server_default=func.now()),
    )

    business: "Business" = Relationship(back_populates="admins")


class AssistantType(str, Enum):
    email = "email"
    chat = "chat"


class Assistant(SQLModel, table=True):
    """Represents an assistant that belongs to a business."""

    id: int = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    openai_assistant_id: str
    start_message: str | None = Field(default=None)  # not used on all assistant types
    instructions: str
    context: str
    model: str
    type: AssistantType
    # Boolean flags for various functions the assistant can use.
    uses_function_check_availability: bool = False
    uses_function_get_product_list: bool = False
    uses_function_get_product_locations: bool = False
    uses_function_get_product_photos: bool = False
    uses_function_set_appointment: bool = False
    uses_handoff_to_admin: bool = False
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    business: "Business" = Relationship(back_populates="assistants")
    conversations: list["Conversation"] = Relationship(back_populates="assistant")


class Conversation(SQLModel, table=True):
    """Represents a conversation related to a business."""

    id: int = Field(default=None, primary_key=True)
    assistant_id: int = Field(default=None, foreign_key="assistant.id")
    thread_id: str
    client_timezone: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    assistant: "Assistant" = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(back_populates="conversation")


message_sequence = Sequence("message_sequence", start=1, increment=1)


class Message(SQLModel, table=True):
    """Represents a message within a conversation."""

    id: int = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"server_default": message_sequence.next_value()},
    )
    conversation_id: int = Field(default=None, foreign_key="conversation.id", index=True)
    role: str
    content: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    conversation: "Conversation" = Relationship(back_populates="messages")


class Associate(SQLModel, table=True):
    """Represents an associate linked to a business."""

    id: int = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    calendar_id: str
    timezone: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    business: "Business" = Relationship(back_populates="associates")
    schedules: list["Schedule"] = Relationship(back_populates="associate")


class Location(SQLModel, table=True):
    """Represents a location related to a business."""

    id: int = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    description: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    business: "Business" = Relationship(back_populates="locations")
    schedules: list["Schedule"] = Relationship(back_populates="location")

    @override
    def __str__(self) -> str:
        """Returns a string representation of the Location."""
        return f"Location:\n\tID: {self.id}\n\tDescription: {self.description}"

    def as_lite_dict(self) -> dict[str, str | int]:
        return {"location_id": self.id, "description": self.description}


class Product(SQLModel, table=True):
    """Represents a product offered by a business."""

    id: int = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    duration_minutes: int
    description: str
    booking_fee: float
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    business: "Business" = Relationship(back_populates="products")

    @override
    def __str__(self) -> str:
        """Returns a string representation of the Product."""
        return f"Product:\n\tID: {self.id}\n\tDescription: {self.description}"

    def as_lite_dict(self) -> dict[str, str | int | float]:
        return {
            "product_id": self.id,
            "description": self.description,
            "duration_minutes": self.duration_minutes,
            "booking_fee": self.booking_fee,
        }


class Photo(SQLModel, table=True):
    """Represents a photo related to a business."""

    id: int | None = Field(default=None, primary_key=True)
    file_uid: str
    description: str
    business_id: int = Field(default=None, foreign_key="business.id")
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime, server_default=func.now()))

    business: "Business" = Relationship(back_populates="photos")

    @override
    def __str__(self) -> str:
        """Returns a string representation of the Photo."""
        return f"Photo:\n\tID: {self.id}\n\tDescription: {self.description}"


class PhotoProductLink(SQLModel, table=True):
    """
    Represents a link between photos and products.
    A product can have multiple photos associated with it,
    and the same photo can be linked to multiple products.
    """

    __tablename__ = "photo_product_link"

    photo_id: int | None = Field(default=None, foreign_key="photo.id", primary_key=True)
    product_id: int | None = Field(default=None, foreign_key="product.id", primary_key=True)
    created_at: datetime | None = Field(default=None, sa_column=Column(DateTime, server_default=func.now()))


class LocationProductLink(SQLModel, table=True):
    """
    Represents a link between locations and products.
    A location can have multiple products, and
    the same product can be found at multiple locations.
    """

    __tablename__ = "location_product_link"

    location_id: int = Field(default=None, foreign_key="location.id", primary_key=True)
    product_id: int = Field(default=None, foreign_key="product.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )


class AssociateProductLink(SQLModel, table=True):
    """
    Represents a link between associates and products.
    An associate can provide multiple products, and
    the same product can be offered by multiple locations.
    """

    __tablename__ = "associate_product_link"

    associate_id: int = Field(default=None, foreign_key="associate.id", primary_key=True)
    product_id: int = Field(default=None, foreign_key="product.id", primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )


class Schedule(SQLModel, table=True):
    """Represents a schedule for an associate at a location."""

    id: int = Field(default=None, primary_key=True)
    associate_id: int = Field(default=None, foreign_key="associate.id")
    location_id: int = Field(default=None, foreign_key="location.id")
    start_datetime: datetime
    end_datetime: datetime
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    associate: "Associate" = Relationship(back_populates="schedules")
    location: "Location" = Relationship(back_populates="schedules")

    @property
    def start_dtz(self) -> datetime:
        """Returns the start datetime localized to UTC."""
        return pytz.UTC.localize(self.start_datetime)

    @property
    def end_dtz(self) -> datetime:
        """Returns the end datetime localized to UTC."""
        return pytz.UTC.localize(self.end_datetime)


class ApiKey(SQLModel, table=True):
    """Represents an API key with an associated business."""

    id: int = Field(default=None, primary_key=True)
    key: str = Field(default_factory=lambda: str(uuid.uuid4()))
    business_id: int = Field(default=None, foreign_key="business.id")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(utc),
        sa_column=Column(DateTime, server_default=func.now()),
    )

    business: "Business" = Relationship(back_populates="api_keys")
