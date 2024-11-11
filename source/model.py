from pydantic import BaseModel


class ConversationInitRequest(BaseModel):
    business_id: int


class ConversationInitResponse(BaseModel):
    conversation_id: int
