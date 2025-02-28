from fastapi import APIRouter, Depends, Header, HTTPException

from source.bedrock_assistant import BedrockAssistant
from source.database import Message
from source.model import ConversationInitRequest, ConversationInitResponse, UserMessageRequest, UserMessageResponse
from source.utils import db

router = APIRouter()


# Dependency (it’s assumed api_key_dependency is defined in main app or utils)
def api_key_dependency(x_api_key: str = Header(...)):
    if not db.validate_api_key(x_api_key):
        raise HTTPException(status_code=403, detail="Invalid API Key")


@router.post(
    "/initialize-conversation/", response_model=ConversationInitResponse, dependencies=[Depends(api_key_dependency)]
)
def initialize_conversation(payload: ConversationInitRequest, x_api_key: str = Header(...)) -> ConversationInitResponse:
    business = db.get_business_by_api_key(x_api_key)
    asst_config = db.get_assistant_by_business_and_type(business.id, "chat")

    # Using BedrockAssistant instead of the OpenAI Assistant
    assistant = BedrockAssistant(
        credentials=None,  # Will use AWS credentials from environment variables
        assistant_id=asst_config.openai_assistant_id,
        client_timezone=payload.client_timezone,
        instructions=asst_config.instructions,
    )

    conversation = db.create_conversation(asst_config.id, payload.client_timezone, assistant.thread.thread_id)
    assert asst_config.start_message is not None
    assistant.add_message({"role": "assistant", "content": asst_config.start_message})

    assistant_first_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=asst_config.start_message,
    )
    db.insert_messages([assistant_first_message])
    return ConversationInitResponse(conversation_id=conversation.id, message=assistant_first_message)


@router.post("/send-message/", response_model=UserMessageResponse, dependencies=[Depends(api_key_dependency)])
def send_message(payload: UserMessageRequest) -> UserMessageResponse:
    conversation, business = db.get_conversation_and_business_by_id(payload.conversation_id)
    db.insert_messages([Message(conversation_id=conversation.id, role="user", content=payload.content)])
    asst_config = db.get_assistant_by_business_and_type(business.id, "chat")

    # Using BedrockAssistant instead of the OpenAI Assistant
    assistant = BedrockAssistant(
        credentials=None,  # Will use AWS credentials from environment variables
        assistant_id=asst_config.openai_assistant_id,
        client_timezone=conversation.client_timezone,
        thread_id=conversation.thread_id,
        instructions=asst_config.instructions,
    )

    message = {"role": "user", "content": payload.content}
    assistant.add_message(message)
    message_response = assistant.retrieve_response()
    new_message = Message(conversation_id=conversation.id, role="assistant", content=message_response)
    db.insert_messages([new_message])
    return UserMessageResponse(message=new_message)
