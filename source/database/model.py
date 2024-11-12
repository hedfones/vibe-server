from datetime import date, time
from typing import List, Optional

import yaml
from sqlalchemy import Sequence
from sqlmodel import Field, Relationship, SQLModel


class Business(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    manifest: Optional[str] = Field(default=None)  # YAML Manifest
    assistant_id: str

    conversations: List["Conversation"] = Relationship(back_populates="business")
    products: List["Product"] = Relationship(back_populates="business")
    associates: List["Associate"] = Relationship(back_populates="business")
    locations: List["Location"] = Relationship(back_populates="business")

    def set_yaml_data(self, data: dict):
        """Convert a Python dictionary to a YAML string and store it."""
        self.manifest = yaml.dump(data)

    def get_yaml_data(self) -> Optional[dict]:
        """Load the YAML string as a Python dictionary."""
        if not self.manifest:
            return
        return yaml.safe_load(self.manifest)


class Conversation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    thread_id: str

    business: "Business" = Relationship(back_populates="conversations")
    messages: List["Message"] = Relationship(back_populates="conversation")


message_sequence = Sequence("message_sequence", start=1, increment=1)


class Message(SQLModel, table=True):
    id: Optional[int] = Field(
        primary_key=True,
        sa_column_kwargs={"server_default": message_sequence.next_value()},
    )
    conversation_id: Optional[int] = Field(
        default=None, foreign_key="conversation.id", index=True
    )
    role: str
    content: str

    conversation: "Conversation" = Relationship(back_populates="messages")


class Associate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")

    business: "Business" = Relationship(back_populates="associates")
    schedules: List["Schedule"] = Relationship(back_populates="associate")
    appointments: List["Schedule"] = Relationship(back_populates="associate")


class Location(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")

    business: "Business" = Relationship(back_populates="locations")
    schedules: List["Schedule"] = Relationship(back_populates="location")


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    business_id: int = Field(default=None, foreign_key="business.id")
    duration_minutes: int

    business: "Business" = Relationship(back_populates="products")


class LocationProductLink(SQLModel, table=True):
    """
    A location can have multiple products, and
    the same product can be found at multiple locations.
    """

    __tablename__ = "location_product_link"

    location_id: Optional[int] = Field(
        default=None, foreign_key="location.id", primary_key=True
    )
    product_id: Optional[int] = Field(
        default=None, foreign_key="product.id", primary_key=True
    )


class AssociateProductLink(SQLModel, table=True):
    """
    An associate can provide multiple products, and
    the same product can be offered by multiple locations.
    """

    __tablename__ = "associate_product_link"

    associate_id: Optional[int] = Field(
        default=None, foreign_key="associate.id", primary_key=True
    )
    product_id: Optional[int] = Field(
        default=None, foreign_key="product.id", primary_key=True
    )


class Schedule(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    associate_id: int = Field(default=None, foreign_key="associate.id")
    location_id: int = Field(default=None, foreign_key="location.id")
    start_time: time
    end_time: time
    effective_on: date
    expires_on: date
    day_of_week: int = Field(
        description="Day of the week as an integer, 0=Monday ... 6=Sunday"
    )

    associate: "Associate" = Relationship(back_populates="schedules")
    location: "Location" = Relationship(back_populates="schedules")


class Appointment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    associate_id: int = Field(default=None, foreign_key="associate.id")
    date: date
    start_time: time
    end_time: time

    associate: "Associate" = Relationship(back_populates="appointments")
