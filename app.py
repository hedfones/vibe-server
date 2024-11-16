from typing import List

from fastapi import FastAPI, HTTPException

from source import (
    Assistant,
    ConversationInitRequest,
    ConversationInitResponse,
    DatabaseService,
    GetAvailabilityRequest,
    GetAvailabilityResponse,
    Message,
    OpenAICredentials,
    PostgresCredentials,
    Product,
    Scheduler,
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

scheduler = Scheduler(db)


@app.post("/initialize-conversation/", response_model=ConversationInitResponse)
def initialize_conversation(
    payload: ConversationInitRequest,
) -> ConversationInitResponse:
    """
    Initialize a new conversation for a specific business.

    - **payload**: The request payload containing the business ID.

    Returns a response containing the conversation ID if successful.

    Raises HTTP 403 if the business with the provided ID is not found.
    """
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(403, f"Business with ID {payload.business_id} not found.")

    # create thread
    assistant = Assistant(openai_creds, business.assistant_id)
    conversation = db.create_conversation(business, assistant.thread.id)

    # get first message from assistant
    # TODO: in future, this intro message should be a static first message for
    #   each assistant
    assistant_first_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=assistant.retrieve_response(),
    )
    db.insert_messages([assistant_first_message])

    # return response
    response = ConversationInitResponse(
        conversation_id=conversation.id,
        message=assistant_first_message
    )
    return response


@app.post("/send-message/", response_model=UserMessageResponse)
def send_message(payload: UserMessageRequest) -> UserMessageResponse:
    """
    Send a message to the assistant in an ongoing conversation.

    - **payload**: The request payload containing the conversation ID and message content.

    Returns a response containing the assistant's reply.

    Raises HTTP 403 if the conversation with the provided ID is not found.
    """
    new_messages = []
    conversation = db.get_conversation_by_id(payload.conversation_id)
    if not conversation:
        raise HTTPException(
            403, f"Conversation with ID {payload.conversation_id} not found."
        )
    business = db.get_business_by_id(conversation.business_id)
    new_messages.append(
        Message(conversation_id=conversation.id, role="user", content=payload.content)
    )

    assistant = Assistant(openai_creds, business.assistant_id, conversation.thread_id)
    message = {"role": "user", "content": payload.content}
    assistant.add_message(message)
    message_response = assistant.retrieve_response()
    new_messages.append(
        Message(
            conversation_id=conversation.id, role="assistant", content=message_response
        )
    )

    db.insert_messages(new_messages)

    response = UserMessageResponse(message=new_messages[-1])
    return response


@app.post("/get-availability/", response_model=GetAvailabilityResponse)
def get_availability(payload: GetAvailabilityRequest) -> GetAvailabilityResponse:
    products: List[Product] = db.select_by_id(Product, payload.product_id)
    product = products.pop(0)
    if not product:
        raise HTTPException(403, f"Unable to find product by id `{payload.product_id}`")

    availabilities = scheduler.get_availabilities(
        product.id, product.duration_minutes, payload.location_id
    )
    if not availabilities:
        raise HTTPException(
            403,
            "Unable to find availabilities associated with location "
            f"`{payload.location_id}` and product `{product.id}`.",
        )

    response = GetAvailabilityResponse(availability_windows=availabilities)
    return response
