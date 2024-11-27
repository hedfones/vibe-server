from datetime import datetime

from fastapi import HTTPException

from .calendar import Event, GoogleCalendar
from .database import Appointment, DatabaseService, PostgresCredentials, Product
from .model import AvailabilityWindow, SetAppointmentsRequest
from .scheduler import Scheduler
from .secret_manager import SecretsManager

secrets = SecretsManager("./.env")

db_creds = PostgresCredentials(
    user=secrets.get("POSTGRES_USER") or "",
    password=secrets.get("POSTGRES_PASSWORD") or "",
    database=secrets.get("POSTGRES_DB") or "",
    host=secrets.get("POSTGRES_HOST") or "",
    port=int(secrets.get("POSTGRES_PORT") or 6543),
)
db = DatabaseService(db_creds)

scheduler = Scheduler(db)


def get_availability(product_id: int, location_id: int) -> list[AvailabilityWindow]:
    products: list[Product] = db.select_by_id(Product, product_id)
    if not products:
        raise HTTPException(404, detail=f"Unable to find product by id `{product_id}`")
    product = products.pop(0)

    availabilities = scheduler.get_availabilities(
        product.id, product.duration_minutes, location_id
    )
    if not availabilities:
        raise HTTPException(
            404,
            detail="Unable to find availabilities associated with location "
            + f"`{location_id}` and product `{product.id}`.",
        )

    return availabilities


def get_product_locations(product_id: int) -> str:
    locations = db.get_locations_by_product_id(product_id)
    if not locations:
        raise HTTPException(
            404, f"Unable to find locations associated with product `{product_id}`."
        )

    location_string = "\n".join(map(str, locations))

    return location_string


def get_product_list(assistant_id: str) -> str:
    products = db.get_products_by_assistant_id(assistant_id)
    product_string = "\n".join(map(str, products))
    return product_string


def set_appointment(request: SetAppointmentsRequest) -> str:
    associate, business = db.get_associate_and_business_by_associate_id(
        request.associate_id
    )
    assert (
        associate is not None
    ), f"Associate not found for ID `{request.associate_id}`."
    assert (
        business is not None
    ), f"Business not found for associate ID `{request.associate_id}`."

    location = db.get_location_by_id(request.location_id)
    assert location is not None, f"Location not found for ID `{request.location_id}`."

    appointment = Appointment(
        associate_id=request.associate_id,
        date=request.day,
        start_time=request.start_time,
        end_time=request.end_time,
    )

    start_datetime = datetime.combine(request.day, request.start_time)
    end_datetime = datetime.combine(request.day, request.end_time)

    if business.calendar_service == "google":
        calendar_id = business.calendar_service_id
        calendar = GoogleCalendar(
            secrets.get(f"GOOGLE_TOKEN_{calendar_id}") or "",
            secrets.get(f"GOOGLE_CREDENTIALS_{calendar_id}") or "",
        )  # TODO: be more thoughtful about this credential process
    else:
        raise HTTPException(
            400, detail=f"Unrecognized calendar service `{business.calendar_service}`."
        )

    event: Event = {
        "summary": request.summary,
        "description": request.description,
        "start": {
            "dateTime": start_datetime.isoformat(),
            "timeZone": "America/New_York",  # TODO: change to dynamic
        },
        "end": {
            "dateTime": end_datetime.isoformat(),
            "timeZone": "America/New_York",  # TODO: change to dynamic
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

    _ = calendar.add_event(associate.calendar_id, event)
    db.insert_appointment(appointment)

    return "Appointment created successfully!"


def get_product_photos(product_id: int) -> str:
    photos = db.get_photos_by_product_id(product_id)
    if not photos:
        return "No photos available for this product."

    photo_string = "\n".join(map(str, photos))

    return photo_string
