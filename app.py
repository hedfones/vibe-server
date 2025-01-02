import json
import logging
from pathlib import Path

import structlog
import yaml
from fastapi import FastAPI, File, HTTPException, Request, UploadFile
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
)
from source.model import ProcessEmailsRequest, SyncNotionRequest, SyncNotionResponse, UpdateAssistantRequest
from source.notion import NotionPage, NotionService
from source.utils import db, get_email_by_business_id, strip_markdown_lines

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

structlog.configure(wrapper_class=structlog.make_filtering_bound_logger(logging.DEBUG))
log = structlog.stdlib.get_logger()

secrets = SecretsManager()
file_manager = FileManager("booking-agent-dev")
notion_service = NotionService(secrets.get("NOTION_AUTH_TOKEN"))

openai_creds = OpenAICredentials(
    api_key=secrets.get("OPENAI_API_KEY"),
    project=secrets.get("OPENAI_PROJECT"),
    organization=secrets.get("OPENAI_ORGANIZATION"),
)


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    # Log the detailed error message
    log.error(f"HTTP Exception (status code: {exc.status_code})", status_code=exc.status_code, description=exc.detail)

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
    asst_config = db.get_assistant_by_business_and_type(business.id, "chat")
    assistant = Assistant(openai_creds, asst_config.openai_assistant_id, payload.client_timezone)
    conversation = db.create_conversation(asst_config.id, payload.client_timezone, assistant.thread.thread_id)
    assert asst_config.start_message is not None
    assistant.add_message({"role": "assistant", "content": asst_config.start_message})

    asst_config = db.get_assistant_by_business_and_type(business.id, "chat")
    assert asst_config.start_message is not None
    assistant_first_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=asst_config.start_message,
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
    conversation, business = db.get_conversation_and_business_by_id(payload.conversation_id)
    new_messages.append(Message(conversation_id=conversation.id, role="user", content=payload.content))

    asst_config = db.get_assistant_by_business_and_type(business.id, "chat")
    assistant = Assistant(
        openai_creds, asst_config.openai_assistant_id, conversation.client_timezone, conversation.thread_id
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
        log.error("Error syncing Notion content", business_id=payload.business_id, exception=str(e))
        raise HTTPException(500, f"Error syncing Notion content: {str(e)}") from e


@app.post("/update-assistant/")
def update_assistant(payload: UpdateAssistantRequest) -> None:
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(404, f"Business with ID {payload.business_id} not found.")
    assistant_configs = db.get_all_assistants_by_business_id(business.id)
    for asst_config in assistant_configs:
        assistant = Assistant(openai_creds, asst_config.openai_assistant_id)
        instructions = f"{asst_config.instructions}\n\n{'-' * 80}\n\n{asst_config.context}"
        assistant_name = f"Vibe - {asst_config.type} - {business.name}"

        assistant_fields: dict[str, bool | str | int] = asst_config.model_dump()

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

        assistant.update_assistant(instructions, assistant_name, asst_config.model, function_definitions)


@app.post("/upload-file/")
async def upload_file(file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload a file to the server to be stored in the S3 bucket.

    - **file**: The file to upload.

    Returns a response with the file UID if successful.
    """
    file_contents = await file.read()
    file_uid = file.filename  # or any unique identifier scheme
    assert file_uid is not None, "File has no filename"
    upload_success = file_manager.upload_file(file_uid, file_contents)

    if not upload_success:
        raise HTTPException(500, "Failed to upload file.")

    return JSONResponse(content={"file_uid": file_uid, "message": "File uploaded successfully."})


@app.get("/read-file/{file_uid}", response_class=FileResponse)
def read_file(file_uid: str) -> FileResponse:
    """
    Retrieve a file from the server/S3 bucket.

    - **file_uid**: The unique identifier of the file to retrieve.

    Returns the file as a response.
    """
    file_bytes = file_manager.get_file(file_uid)
    if file_bytes is None:
        raise HTTPException(404, f"File with UID {file_uid} not found.")

    # Save the file_bytes temporarily to return as FileResponse
    tmp_file_path = Path("/tmp") / file_uid
    _ = tmp_file_path.write_bytes(file_bytes)
    return FileResponse(tmp_file_path, filename=file_uid)


@app.post("/process-unread-emails/")
def process_unread_emails(payload: ProcessEmailsRequest) -> dict[str, int]:
    """
    Process unread emails for a business and generate AI responses.

    Args:
        payload: Request containing business_id

    Returns:
        Dictionary with count of processed emails
    """
    # Get business and verify it exists
    business = db.get_business_by_id(payload.business_id)
    if not business:
        raise HTTPException(404, f"Business with ID {payload.business_id} not found.")

    # Initialize Gmail service using business credentials
    mailbox = get_email_by_business_id(payload.business_id)

    # Get unread emails
    unread_emails = mailbox.list_emails(query="is:unread")

    # Initialize assistant for generating responses
    asst_config = db.get_assistant_by_business_and_type(payload.business_id, "email")
    tz = db.get_first_associate_timezone_by_business_id(payload.business_id)
    assistant = Assistant(openai_creds, asst_config.openai_assistant_id, tz)
    conversation = db.create_conversation(asst_config.id, tz, assistant.thread.thread_id)

    processed_count = 0
    thread_ids = set(m["threadId"] for m in unread_emails)
    for thread_id in thread_ids:
        # Get full email content
        thread = mailbox.get_messages_in_thread(thread_id)
        if not thread:
            continue

        # Generate AI response using assistant
        messages: list[Message] = []
        for email in thread:
            message: AssistantMessage = {"role": "user", "content": json.dumps(email)}
            assistant.add_message(message)
            messages.append(Message(**message, conversation_id=conversation.id))
        response = assistant.retrieve_response()
        messages.append(Message(conversation_id=conversation.id, role="assistant", content=response))
        db.insert_messages(messages)

        message_id = thread[-1]["message_id"]
        response_payload: dict[str, str] = json.loads(strip_markdown_lines(response))
        response_payload["to"] = "kalebjs@proton.me"

        # Extract email address from headers
        mailbox.send_email(
            to=response_payload["to"],
            subject=response_payload["subject"],
            body=response_payload["body"],
            message_id=message_id,
            thread_id=thread_id,
            is_html=True,
        )
        processed_count += 1

    return {"processed_emails": processed_count}
