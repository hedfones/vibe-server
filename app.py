from fastapi import FastAPI, HTTPException

from source import ConversationInitRequest, ConversationInitResponse, DatabaseService

app = FastAPI()
db = DatabaseService()


@app.post("/initialize-conversation/")
def initialize_conversation(
    payload: ConversationInitRequest,
) -> ConversationInitResponse:
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(403, f"Business with ID {payload.business_id} not found.")
    conversation = db.create_conversation(business)
    response = ConversationInitResponse(conversation_id=conversation.id)
    return response
