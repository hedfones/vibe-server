import json

import pytz
import structlog
from fastapi import HTTPException

from .database import DatabaseService, PostgresCredentials, Product
from .google_service import Event, GoogleCalendar
from .model import AvailabilityWindow, SetAppointmentsRequest
from .scheduler import Scheduler
from .secret_manager import SecretsManager

log = structlog.stdlib.get_logger()

# Initialize SecretsManager to manage access to sensitive credentials
secrets = SecretsManager()

# Set up database credentials using secrets manager
db_creds = PostgresCredentials(
    user=secrets.get("POSTGRES_USER"),
    password=secrets.get("POSTGRES_PASSWORD"),
    database=secrets.get("POSTGRES_DB"),
    host=secrets.get("POSTGRES_HOST"),
    port=int(secrets.get("POSTGRES_PORT")),
)
db = DatabaseService(db_creds)


def get_google_calendar_by_calendar_id(calendar_id: str) -> GoogleCalendar:
    secret_name = f"GOOGLE_OAUTH2_{calendar_id}"
    creds = secrets.get_raw(secret_name)
    callback = secrets.get_update_callback(secret_name)
    secret, token = creds["secret"], creds.get("token")
    token = json.dumps(token) if token else None
    return GoogleCalendar.from_oauth2(json.dumps(secret), token, callback)


def get_calendar_by_business_id(business_id: int) -> GoogleCalendar:
    """Fetch Google Calendar for a given business ID.

    Args:
        business_id (int): The ID of the business.

    Returns:
        GoogleCalendar: An instance of GoogleCalendar configured with credentials.

    Raises:
        HTTPException: If the business or Google Calendar credentials are not found.
    """
    logger = log.bind(business_id=business_id)
    logger.debug("Fetching calendar by business ID.")
    business = db.get_business_by_id(business_id)
    assert business is not None, f"Business not found for ID `{business_id}`."

    if business.calendar_service == "google":
        logger.debug("Business uses Google Calendar service.")
        calendar_id = business.calendar_service_id

        # Fetch the Google service account credentials for the calendar
        return get_google_calendar_by_calendar_id(calendar_id)
    else:
        logger.error("Unrecognized calendar service.", service=business.calendar_service)
        raise HTTPException(400, detail=f"Unrecognized calendar service `{business.calendar_service}`.")


def get_availability(product_id: int, location_id: int, timezone: str) -> list[AvailabilityWindow]:
    """Retrieve availability windows for a product at a specific location.

    Args:
        product_id (int): The ID of the product.
        location_id (int): The ID of the location.
        timezone (str): The timezone for localization.

    Returns:
        list[AvailabilityWindow]: A list of available time windows for the product.

    Raises:
        HTTPException: If no product or availabilities are found.
    """
    logger = log.bind(product_id=product_id, location_id=location_id, timezone=timezone)
    logger.debug("Fetching availability for product ID at location ID in timezone.")
    products: list[Product] = db.select_by_id(Product, product_id)
    if not products:
        logger.error("Product not found.")
        raise HTTPException(404, detail=f"Unable to find product by id `{product_id}`")
    product = products.pop(0)

    calendar = get_calendar_by_business_id(product.business_id)
    scheduler = Scheduler(db, calendar)

    # Get availability windows using the scheduler
    availabilities = scheduler.get_availabilities(product.id, product.duration_minutes, location_id)
    if not availabilities:
        logger.error("No availabilities found.", duration_minutes=product.duration_minutes, location_id=location_id)
        raise HTTPException(
            404,
            detail="Unable to find availabilities associated with location "
            + f"`{location_id}` and product `{product.id}`.",
        )

    # Localize availability times to the specified timezone
    for availability in availabilities:
        availability.localize(timezone)

    logger.debug("Availabilities fetched successfully.")
    return availabilities


def get_product_locations(product_id: int) -> str:
    """Fetch locations where a product is available.

    Args:
        product_id (int): The ID of the product.

    Returns:
        str: A string representation of the locations.

    Raises:
        HTTPException: If no locations are found for the product.
    """
    logger = log.bind(product_id=product_id)
    logger.debug("Fetching locations by product ID.")
    locations = db.get_locations_by_product_id(product_id)
    if not locations:
        logger.error("Locations not found.")
        raise HTTPException(404, f"Unable to find locations associated with product `{product_id}`.")

    location_string = "\n".join(map(str, locations))

    logger.debug("Locations fetched successfully.")
    return location_string


def get_product_list(assistant_id: str) -> str:
    """Retrieve a list of products managed by a specific assistant.

    Args:
        assistant_id (str): The ID of the assistant.

    Returns:
        str: A string representation of the product list.
    """
    log.debug("Fetching product list for assistant ID.", assistant_id=assistant_id)
    products = db.get_products_by_assistant_id(assistant_id)
    product_string = "\n".join(map(str, products))

    log.debug("Product list fetched successfully.")
    return product_string


def set_appointment(request: SetAppointmentsRequest) -> str:
    """Set an appointment in the calendar based on the provided request.

    Args:
        request (SetAppointmentsRequest): The details of the appointment to set.

    Returns:
        str: Confirmation message upon successful appointment setting.

    Raises:
        HTTPException: If resources like associate, business, or location are not found.
    """
    logger = log.bind(request=request)
    logger.debug("Setting appointment with request.")
    associate, business = db.get_associate_and_business_by_associate_id(request.associate_id)
    assert associate is not None, f"Associate not found for ID `{request.associate_id}`."
    assert business is not None, f"Business not found for associate ID `{request.associate_id}`."

    location = db.get_location_by_id(request.location_id)
    assert location is not None, f"Location not found for ID `{request.location_id}`."

    # Convert requested start and end times to UTC
    start_datetime = request.start_datetime.astimezone(pytz.utc)
    end_datetime = request.end_datetime.astimezone(pytz.utc)

    logger = logger.bind(calendar_service=business.calendar_service)
    calendar = get_calendar_by_business_id(business.id)

    # Define the event with necessary details
    event: Event = {
        "summary": request.summary,
        "description": request.description,
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "UTC",
        },
        "attendees": [{"email": email} for email in request.attendee_emails],
        "location": location.description,
        "reminders": {
            "useDefault": False,
            "overrides": [
                {"method": "email", "minutes": 24 * 60},  # 1 day before
                {"method": "popup", "minutes": 10},  # 10 minutes before
            ],
        },
    }

    # Add the event to the calendar
    event = calendar.add_event(associate.calendar_id, event)
    assert "id" in event, "Event is missing ID field"

    logger.debug("Appointment created successfully.")
    return "Appointment created successfully!"


def get_product_photos(product_id: int) -> str:
    """Fetch photos associated with a product.

    Args:
        product_id (int): The ID of the product.

    Returns:
        str: A string representation of the photos or a message if none are available.
    """
    log.debug("Fetching photos for product ID.", product_id=product_id)
    photos = db.get_photos_by_product_id(product_id)
    if not photos:
        log.warning("No photos available.")
        return "No photos available for this product."

    photo_string = "\n".join(map(str, photos))

    log.debug("Photos fetched successfully.")
    return photo_string
