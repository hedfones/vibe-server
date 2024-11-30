import logging
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from source import (
    Appointment,
    Assistant,
    AssistantMessage,
    ConversationInitRequest,
    ConversationInitResponse,
    Event,
    Message,
    OpenAICredentials,
    Scheduler,
    SecretsManager,
    UserMessageRequest,
    UserMessageResponse,
    db,
    event_to_appointment,
    get_calendar_by_business_id,
)

app = FastAPI()
# Add CORSMiddleware to allow requests from the client
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080"
    ],  # Change this to the URL of your Vue.js app
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],  # Allows all headers
)

secrets = SecretsManager("./.env")

openai_creds = OpenAICredentials(
    api_key=secrets.get("OPENAI_API_KEY") or "",
    project=secrets.get("OPENAI_PROJECT") or "",
    organization=secrets.get("OPENAI_ORGANIZATION") or "",
)

scheduler = Scheduler(db)

logging.basicConfig(level=logging.INFO)


@app.exception_handler(HTTPException)
def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    # Log the detailed error message
    logging.error(f"HTTP Exception: {exc.detail} (status code: {exc.status_code})")

    # Return the original error response
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


@app.post("/initialize-conversation/", response_model=ConversationInitResponse)
def initialize_conversation(
    payload: ConversationInitRequest,
) -> ConversationInitResponse:
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
    assistant = Assistant(openai_creds, business.assistant_id)
    conversation = db.create_conversation(business, assistant.thread.id)

    # get first message from assistant
    # TODO: in future, this intro message should be a static first message for
    #   each assistant
    assistant_first_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=business.start_message,
    )
    db.insert_messages([assistant_first_message])

    # return response
    response = ConversationInitResponse(
        conversation_id=conversation.id, message=assistant_first_message
    )
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
        raise HTTPException(
            404, f"Conversation with ID {payload.conversation_id} not found."
        )

    business = db.get_business_by_id(conversation.business_id)
    if not business:
        raise HTTPException(
            404, f"Business with ID {conversation.business_id} not found."
        )
    new_messages.append(
        Message(conversation_id=conversation.id, role="user", content=payload.content)
    )

    assistant = Assistant(openai_creds, business.assistant_id, conversation.thread_id)
    message: AssistantMessage = {"role": "user", "content": payload.content}
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


@app.get("/sync-calendars/")
def sync_calendars() -> JSONResponse:
    """
    Sync calendars for all associates by converting events into appointments.

    Retrieves all associates from the database, gets their calendar IDs,
    and reads all events to convert them into appointments.
    """
    associates = db.get_all_associates()
    appointments = []

    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now() + timedelta(days=366)

    for associate in associates:
        calendar = get_calendar_by_business_id(associate.business_id)
        events = calendar.read_appointments(associate.calendar_id, start_date, end_date)
        appointments = db.get_appointments_by_associate_id(associate.id)

        calendar_id_to_appointment: dict[str, Appointment] = {
            appointment.calendar_id: appointment for appointment in appointments
        }
        calendar_id_to_event: dict[str, Event] = {
            event["id"]: event for event in events
        }

        appointment_calendar_ids: set[str] = set(calendar_id_to_appointment.keys())
        event_calendar_ids: set[str] = set(calendar_id_to_event.keys())

        removed_from_calendar_appointments = appointment_calendar_ids.difference(
            event_calendar_ids
        )
        added_to_calendar = event_calendar_ids.difference(appointment_calendar_ids)
        common = event_calendar_ids.intersection(appointment_calendar_ids)

        for event_id in removed_from_calendar_appointments:
            appointment = calendar_id_to_appointment[event_id]
            db.delete_appointment_by_calendar_id(appointment.calendar_id)
            logging.info(
                f"Appointment with calendar ID {appointment.calendar_id} deleted because it was removed by user from their calendar."
            )

        new_appointments: list[Appointment] = []
        for event_id in added_to_calendar:
            event = calendar_id_to_event[event_id]
            appointment = event_to_appointment(event, associate.id)
            new_appointments.append(appointment)
            logging.info(f"Found new appointment {event['summary']}")
        db.insert_appointments(new_appointments)

        for event_id in common:
            appointment = calendar_id_to_appointment[event_id]
            event = calendar_id_to_event[event_id]
            event_start = datetime.fromisoformat(event["start"]["dateTime"])
            event_end = datetime.fromisoformat(event["end"]["dateTime"])
            appointment_start = datetime.combine(
                appointment.date, appointment.start_time
            )
            appointment_end = datetime.combine(appointment.date, appointment.end_time)

            if event_start != appointment_start or event_end != appointment_end:
                appointment.start_time = event_start.time()
                appointment.end_time = event_end.time()
                db.update_appointment(appointment)
                logging.info(
                    f"Updated appointment with calendar ID {appointment.calendar_id} to reflect changes in the calendar."
                )

    return JSONResponse(content={"message": "👍"})
