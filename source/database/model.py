from datetime import date, datetime, time

from sqlalchemy import Column, DateTime, Sequence, func
from sqlmodel import Field, Relationship, SQLModel
from typing_extensions import override


class Business(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    assistant_id: str
    start_message: str
    instructions: str
    calendar_service: str
    calendar_service_id: str
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    conversations: list["Conversation"] = Relationship(back_populates="business")
    products: list["Product"] = Relationship(back_populates="business")
    associates: list["Associate"] = Relationship(back_populates="business")
    locations: list["Location"] = Relationship(back_populates="business")


class Conversation(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    thread_id: str
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    business: "Business" = Relationship(back_populates="conversations")
    messages: list["Message"] = Relationship(back_populates="conversation")


message_sequence = Sequence("message_sequence", start=1, increment=1)


class Message(SQLModel, table=True):
    id: int | None = Field(
        default=None,
        primary_key=True,
        sa_column_kwargs={"server_default": message_sequence.next_value()},
    )
    conversation_id: int = Field(
        default=None, foreign_key="conversation.id", index=True
    )
    role: str
    content: str
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    conversation: "Conversation" = Relationship(back_populates="messages")


class Associate(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    calendar_id: str
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    business: "Business" = Relationship(back_populates="associates")
    schedules: list["Schedule"] = Relationship(back_populates="associate")
    appointments: list["Appointment"] = Relationship(back_populates="associate")


class Location(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    description: str
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    business: "Business" = Relationship(back_populates="locations")
    schedules: list["Schedule"] = Relationship(back_populates="location")

    @override
    def __str__(self) -> str:
        return f"Location:\n\tID: {self.id}\n\tDescription: {self.description}"


class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    duration_minutes: int
    description: str
    booking_fee: float
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    business: "Business" = Relationship(back_populates="products")

    @override
    def __str__(self) -> str:
        return f"Product:\n\tID: {self.id}\n\tDescription: {self.description}"


class LocationProductLink(SQLModel, table=True):
    """
    A location can have multiple products, and
    the same product can be found at multiple locations.
    """

    __tablename__ = "location_product_link"

    location_id: int | None = Field(
        default=None, foreign_key="location.id", primary_key=True
    )
    product_id: int | None = Field(
        default=None, foreign_key="product.id", primary_key=True
    )
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date


class AssociateProductLink(SQLModel, table=True):
    """
    An associate can provide multiple products, and
    the same product can be offered by multiple locations.
    """

    __tablename__ = "associate_product_link"

    associate_id: int | None = Field(
        default=None, foreign_key="associate.id", primary_key=True
    )
    product_id: int | None = Field(
        default=None, foreign_key="product.id", primary_key=True
    )
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date


class Schedule(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    associate_id: int = Field(default=None, foreign_key="associate.id")
    location_id: int = Field(default=None, foreign_key="location.id")
    start_time: time
    end_time: time
    effective_on: date
    expires_on: date
    day_of_week: int = Field(
        description="Day of the week as an integer, 0=Sunday ... 6=Saturday"
    )
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    associate: "Associate" = Relationship(back_populates="schedules")
    location: "Location" = Relationship(back_populates="schedules")


class Appointment(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    associate_id: int = Field(default=None, foreign_key="associate.id")
    date: date
    start_time: time
    end_time: time
    created_at: datetime | None = Field(
        default=None, sa_column=Column(DateTime, server_default=func.now())
    )  # Creation date

    associate: "Associate" = Relationship(back_populates="appointments")
