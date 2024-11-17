from datetime import datetime

from pydantic import BaseModel

from .database import Message


class ConversationInitRequest(BaseModel):
    """Request model for initializing a conversation.

    Attributes:
        business_id (int): The ID of the business initiating the conversation.
    """

    business_id: int


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

    def __str__(self) -> str:
        return (
            "Availability Window:\n"
            f"\tDate: {self.start_time.strftime('%A, %B %d, %Y')}\n"
            f"\tStart Time: {self.start_time.strftime('%H:%M:%S')}\n"
            f"\tEnd Time: {self.end_time.strftime('%H:%M:%S')}\n"
            f"\tAssociate ID: {self.associate_id}"
        )
