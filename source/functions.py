import pytz
from fastapi import HTTPException

from .calendar_service import Event, GoogleCalendar
from .database import DatabaseService, PostgresCredentials, Product
from .logger import logger
from .model import AvailabilityWindow, SetAppointmentsRequest
from .scheduler import Scheduler
from .secret_manager import SecretsManager

secrets = SecretsManager()

db_creds = PostgresCredentials(
    user=secrets.get("POSTGRES_USER") or "",
    password=secrets.get("POSTGRES_PASSWORD") or "",
    database=secrets.get("POSTGRES_DB") or "",
    host=secrets.get("POSTGRES_HOST") or "",
    port=int(secrets.get("POSTGRES_PORT") or 6543),
)
db = DatabaseService(db_creds)


def get_calendar_by_business_id(business_id: int) -> GoogleCalendar:
    logger.debug(f"Fetching calendar for business ID {business_id}.")
    business = db.get_business_by_id(business_id)
    assert business is not None, f"Business not found for ID `{business_id}`."

    if business.calendar_service == "google":
        logger.debug("Business uses Google Calendar service.")
        calendar_id = business.calendar_service_id
        service_account = secrets.get(f"GOOGLE_SERVICE_ACCOUNT_{calendar_id}")
        if not service_account:
            logger.error("Google Calendar credentials not found.")
            raise HTTPException(
                status_code=500, detail=f"Google Calendar credentials not found for calendar ID: {calendar_id}"
            )
        return GoogleCalendar(service_account_base64=service_account)
    else:
        logger.error("Unrecognized calendar service.")
        raise HTTPException(400, detail=f"Unrecognized calendar service `{business.calendar_service}`.")


def get_availability(product_id: int, location_id: int, timezone: str) -> list[AvailabilityWindow]:
    logger.debug(
        f"Fetching availability for product ID {product_id} at location ID {location_id} in timezone {timezone}."
    )
    products: list[Product] = db.select_by_id(Product, product_id)
    if not products:
        logger.error("Product not found.")
        raise HTTPException(404, detail=f"Unable to find product by id `{product_id}`")
    product = products.pop(0)

    calendar = get_calendar_by_business_id(product.business_id)
    scheduler = Scheduler(db, calendar)

    availabilities = scheduler.get_availabilities(product.id, product.duration_minutes, location_id)
    if not availabilities:
        logger.error("No availabilities found.")
        raise HTTPException(
            404,
            detail="Unable to find availabilities associated with location "
            + f"`{location_id}` and product `{product.id}`.",
        )

    for availability in availabilities:
        availability.localize(timezone)

    logger.debug("Availabilities fetched successfully.")
    return availabilities


def get_product_locations(product_id: int) -> str:
    logger.debug(f"Fetching locations for product ID {product_id}.")
    locations = db.get_locations_by_product_id(product_id)
    if not locations:
        logger.error("Locations not found.")
        raise HTTPException(404, f"Unable to find locations associated with product `{product_id}`.")

    location_string = "\n".join(map(str, locations))

    logger.debug("Locations fetched successfully.")
    return location_string


def get_product_list(assistant_id: str) -> str:
    logger.debug(f"Fetching product list for assistant ID {assistant_id}.")
    products = db.get_products_by_assistant_id(assistant_id)
    product_string = "\n".join(map(str, products))

    logger.debug("Product list fetched successfully.")
    return product_string


def set_appointment(request: SetAppointmentsRequest) -> str:
    logger.debug(f"Setting appointment with request: {request}.")
    associate, business = db.get_associate_and_business_by_associate_id(request.associate_id)
    assert associate is not None, f"Associate not found for ID `{request.associate_id}`."
    assert business is not None, f"Business not found for associate ID `{request.associate_id}`."

    location = db.get_location_by_id(request.location_id)
    assert location is not None, f"Location not found for ID `{request.location_id}`."

    start_datetime = request.start_datetime.astimezone(pytz.utc)
    end_datetime = request.end_datetime.astimezone(pytz.utc)

    if business.calendar_service == "google":
        logger.debug("Using Google Calendar service for appointment.")
        calendar_id = business.calendar_service_id
        calendar = GoogleCalendar(
            service_account_base64=secrets.get(f"GOOGLE_SERVICE_ACCOUNT_{calendar_id}") or "",
        )  # TODO: be more thoughtful about this credential process
    else:
        logger.error("Unrecognized calendar service for appointment.")
        raise HTTPException(400, detail=f"Unrecognized calendar service `{business.calendar_service}`.")
    calendar = get_calendar_by_business_id(business.id)

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

    event = calendar.add_event(associate.calendar_id, event)
    assert "id" in event, "Event is missing ID field"

    logger.debug("Appointment created successfully.")
    return "Appointment created successfully!"


def get_product_photos(product_id: int) -> str:
    logger.debug(f"Fetching photos for product ID {product_id}.")
    photos = db.get_photos_by_product_id(product_id)
    if not photos:
        logger.warning("No photos available.")
        return "No photos available for this product."

    photo_string = "\n".join(map(str, photos))

    logger.debug("Photos fetched successfully.")
    return photo_string
