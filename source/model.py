from datetime import datetime
from typing import List

from pydantic import BaseModel


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


class UserMessageRequest(BaseModel):
    conversation_id: int
    content: str


class UserMessageResponse(BaseModel):
    content: str


class GetAvailabilityRequest(BaseModel):
    location_id: int
    product_id: int


class AvailabilityWindow(BaseModel):
    start_time: datetime
    end_time: datetime
    associate_id: int | None = None

    @property
    def duration_minutes(self) -> float:
        timedelta = self.end_time - self.start_time
        return abs(timedelta.total_seconds()) // 60


class GetAvailabilityResponse(BaseModel):
    availability_windows: List[AvailabilityWindow]
