import json
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from openai.types.shared_params.function_definition import FunctionDefinition

from source import (
    Assistant,
    AssistantMessage,
    ConversationInitRequest,
    ConversationInitResponse,
    FileManager,
    GetPhotoRequest,
    Message,
    OpenAICredentials,
    SecretsManager,
    UserMessageRequest,
    UserMessageResponse,
    db,
    logger,
)
from source.model import SyncNotionRequest, SyncNotionResponse, UpdateAssistantRequest
from source.notion import NotionPage, NotionService

app = FastAPI()
# Add CORSMiddleware to allow requests from the client
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://hedfones.netlify.app",
        "http://localhost:8080",
        "https://app.hedfones.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

secrets = SecretsManager()
file_manager = FileManager("./temp")
notion_service = NotionService(secrets.get("NOTION_AUTH_TOKEN"))

openai_creds = OpenAICredentials(
    api_key=secrets.get("OPENAI_API_KEY"),
    project=secrets.get("OPENAI_PROJECT"),
    organization=secrets.get("OPENAI_ORGANIZATION"),
)


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    # Log the detailed error message
    logger.error(f"HTTP Exception: {exc.detail} (status code: {exc.status_code})")

    # Return the original error response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.post("/initialize-conversation/", response_model=ConversationInitResponse)
def initialize_conversation(payload: ConversationInitRequest) -> ConversationInitResponse:
    """
    Initialize a new conversation for a specific business.

    - **payload**: The request payload containing the business ID.

    Returns a response containing the conversation ID if successful.

    Raises HTTP 404 if the business with the provided ID is not found.
    """
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(404, f"Business with ID {payload.business_id} not found.")

    # create thread
    assistant = Assistant(openai_creds, business.assistant.openai_assistant_id, payload.client_timezone)
    conversation = db.create_conversation(business, payload.client_timezone, assistant.thread.thread_id)
    # assistant.add_message({"role": "system", "content": business.context})
    assistant.add_message({"role": "assistant", "content": business.assistant.start_message})

    assistant_first_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=business.assistant.start_message,
    )
    db.insert_messages([assistant_first_message])

    # return response
    response = ConversationInitResponse(conversation_id=conversation.id, message=assistant_first_message)
    return response


@app.post("/send-message/", response_model=UserMessageResponse)
def send_message(payload: UserMessageRequest) -> UserMessageResponse:
    """
    Send a message to the assistant in an ongoing conversation.

    - **payload**: The request payload containing the conversation ID and message content.

    Returns a response containing the assistant's reply.

    Raises HTTP 404 if the conversation with the provided ID is not found.
    """
    new_messages: list[Message] = []
    conversation = db.get_conversation_by_id(payload.conversation_id)
    if not conversation:
        raise HTTPException(404, f"Conversation with ID {payload.conversation_id} not found.")

    business = db.get_business_by_id(conversation.business_id)
    if not business:
        raise HTTPException(404, f"Business with ID {conversation.business_id} not found.")
    new_messages.append(Message(conversation_id=conversation.id, role="user", content=payload.content))

    assistant = Assistant(
        openai_creds, business.assistant.openai_assistant_id, conversation.client_timezone, conversation.thread_id
    )
    message: AssistantMessage = {"role": "user", "content": payload.content}
    assistant.add_message(message)
    message_response = assistant.retrieve_response()
    new_messages.append(Message(conversation_id=conversation.id, role="assistant", content=message_response))

    db.insert_messages(new_messages)

    response = UserMessageResponse(message=new_messages[-1])
    return response


@app.post("/get-photo/")
def get_photo(payload: GetPhotoRequest) -> FileResponse:
    photo = db.get_photo_by_id(payload.photo_id)
    if photo is None:
        raise HTTPException(404, f"Photo with ID {payload.photo_id} not found.")
    file = file_manager.get_file(photo.file_uid)
    return FileResponse(file, filename=file.name)


@app.post("/sync-notion/", response_model=SyncNotionResponse)
def sync_notion(payload: SyncNotionRequest) -> SyncNotionResponse:
    """
    Sync Notion content for a business.

    - **business_id**: The ID of the business to sync Notion content for

    Returns the synced markdown content.

    Raises HTTP 404 if the business is not found or if the Notion page ID is not set.
    """
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(404, f"Business with ID {payload.business_id} not found.")

    if not business.notion_page_id:
        raise HTTPException(404, f"Business {payload.business_id} does not have a Notion page ID set.")

    try:
        # Get the content from Notion
        notion_page = notion_service.get_page_content(business.notion_page_id)

        def get_page_markdown(page: NotionPage) -> str:
            child_markdown = "\n---\n".join(get_page_markdown(child) for child in page.children)
            markdown = f"{page.markdown}\n---\n*Child Pages*:\n---\n{child_markdown}\n"
            return markdown

        pages: str = get_page_markdown(notion_page)

        # Update the business context with the markdown content
        db.update_assistant_context(payload.business_id, pages)

        return SyncNotionResponse(markdown_content=notion_page)
    except Exception as e:
        logger.error(f"Error syncing Notion content for business {payload.business_id}: {str(e)}")
        raise HTTPException(500, f"Error syncing Notion content: {str(e)}") from e


@app.post("/update-assistant/")
def update_assistant(payload: UpdateAssistantRequest) -> None:
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(404, f"Business with ID {payload.business_id} not found.")
    assistant = Assistant(openai_creds, business.assistant.openai_assistant_id)
    instructions = f"{business.assistant.instructions}\n\n{'-' * 80}\n\n{business.assistant.context}"
    assistant_name = f"Vibe - {business.name}"

    assistant_fields: dict[str, bool | str | int] = business.assistant.model_dump()

    function_dir = Path("resources/functions")
    try:
        with open(function_dir / "function_mapping.yaml", "r") as f:
            function_fields: dict[str, str] = yaml.safe_load(f)
    except FileNotFoundError as e:
        raise HTTPException(500, "Function mapping file not found.") from e
    except yaml.YAMLError as e:
        raise HTTPException(500, f"Error parsing function mapping file: {e}") from e

    function_definitions: list[FunctionDefinition] = []
    for key, filename in function_fields.items():
        do_use_function = assistant_fields[key]
        if not do_use_function:
            continue
        filepath = function_dir / filename
        try:
            with filepath.open("r") as f:
                function_definition: FunctionDefinition = json.load(f)
        except FileNotFoundError as e:
            raise HTTPException(500, f"Function definition file {filename} not found.") from e
        except json.JSONDecodeError as e:
            raise HTTPException(500, f"Error parsing function definition file {filename}: {e}") from e

        function_definitions.append(function_definition)

    assistant.update_assistant(instructions, assistant_name, business.assistant.model, function_definitions)
