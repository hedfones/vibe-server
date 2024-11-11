from fastapi import FastAPI, HTTPException

from source import (
    Assistant,
    ConversationInitRequest,
    ConversationInitResponse,
    DatabaseService,
    OpenAICredentials,
    PostgresCredentials,
    SecretsManager,
    UserMessageRequest,
    UserMessageResponse,
)

app = FastAPI()
secrets = SecretsManager("./.env")

db_creds = PostgresCredentials(
    user=secrets.get("POSTGRES_USER"),
    password=secrets.get("POSTGRES_PASSWORD"),
)
db = DatabaseService(db_creds)

openai_creds = OpenAICredentials(
    api_key=secrets.get("OPENAI_API_KEY"),
    project=secrets.get("OPENAI_PROJECT_ID"),
    organization=secrets.get("OPENAI_ORGANIZATION_ID"),
)


@app.post("/initialize-conversation/")
def initialize_conversation(
    payload: ConversationInitRequest,
) -> ConversationInitResponse:
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(403, f"Business with ID {payload.business_id} not found.")
    assistant = Assistant(openai_creds, business.assistant_id)
    conversation = db.create_conversation(business, assistant.thread.id)
    response = ConversationInitResponse(conversation_id=conversation.id)
    return response


@app.post("/send-message/")
def send_message(payload: UserMessageRequest) -> UserMessageResponse: ...
