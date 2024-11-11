from typing import List, Optional

import yaml
from sqlalchemy import Sequence
from sqlmodel import Field, Relationship, SQLModel


class Business(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    manifest: Optional[str] = Field(default=None)  # YAML Manifest
    assistant_id: str

    conversations: List["Conversation"] = Relationship(back_populates="business")

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
