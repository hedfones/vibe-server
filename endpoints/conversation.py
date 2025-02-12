from fastapi import APIRouter, Depends, Header, HTTPException

from source import Assistant, OpenAICredentials
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
    openai_creds = OpenAICredentials(api_key="YOUR_API_KEY", project="YOUR_PROJECT", organization="YOUR_ORG")
    assistant = Assistant(openai_creds, asst_config.openai_assistant_id, payload.client_timezone)
    conversation = db.create_conversation(asst_config.id, payload.client_timezone, assistant.thread.thread_id)
    assert asst_config.start_message is not None
    assistant.add_message({"role": "assistant", "content": asst_config.start_message})
    from source.database import Message  # Import here if needed

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
    openai_creds = OpenAICredentials(api_key="YOUR_API_KEY", project="YOUR_PROJECT", organization="YOUR_ORG")
    assistant = Assistant(
        openai_creds, asst_config.openai_assistant_id, conversation.client_timezone, conversation.thread_id
    )
    message = {"role": "user", "content": payload.content}
    assistant.add_message(message)
    message_response = assistant.retrieve_response()
    new_message = Message(conversation_id=conversation.id, role="assistant", content=message_response)
    db.insert_messages([new_message])
    return UserMessageResponse(message=new_message)
