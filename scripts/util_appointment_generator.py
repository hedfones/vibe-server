import os
import random
import sys
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from source import db
from source.database.model import (
    Appointment,
    Associate,
    AssociateProductLink,
    Product,
    Schedule,
)
from source.calendar import GoogleCalendar  # Import GoogleCalendar
from source.secret_manager import SecretsManager  # Import SecretsManager

# Replace with your actual database URL
engine = db.engine
secrets = SecretsManager("./.env")  # Initialize SecretsManager

def get_dates_between(start_date: date, end_date: date, day_of_week: int) -> list[date]:
    """
    Returns a list of dates between start_date and end_date that fall on day_of_week.
    Day_of_week: 0=Monday, ..., 6=Sunday
    """
    dates: list[date] = []
    current_date = start_date
    delta = timedelta(days=1)
    while current_date <= end_date:
        if current_date.weekday() == day_of_week:
            dates.append(current_date)
        current_date += delta
    return dates

def get_calendar(associate_id: int) -> GoogleCalendar:
    """Get Google Calendar instance for the associate."""
    associate: Associate = db.select_by_id(Associate, associate_id)[0]
    business = db.get_business_by_id(associate.business_id)
    calendar_id = business.calendar_service_id

    return GoogleCalendar(
        secrets.get(f"GOOGLE_TOKEN_{calendar_id}") or "",
        secrets.get(f"GOOGLE_CREDENTIALS_{calendar_id}") or "",
    )

def generate_appointments():
    with Session(engine) as session:
        # Get all associates
        associates = session.exec(select(Associate)).all()
        for associate in associates:
            print(f"Generating appointments for Associate ID: {associate.id}")
            # Get the products the associate offers
            product_durations = session.exec(
                select(Product.duration_minutes)
                .join(
                    AssociateProductLink, Product.id == AssociateProductLink.product_id
                )
                .where(AssociateProductLink.associate_id == associate.id)
            ).all()
            # Get unique durations, sorted descending
            durations = sorted(list(product_durations), reverse=True)
            if not durations:
                print(f"No products found for Associate ID: {associate.id}")
                continue
            # Get the associate's schedules
            schedules = session.exec(
                select(Schedule).where(Schedule.associate_id == associate.id)
            ).all()
            if not schedules:
                print(f"No schedules found for Associate ID: {associate.id}")
                continue

            calendar = get_calendar(associate.id)  # Get Google Calendar object

            for schedule in schedules:
                # Determine start_date and end_date
                today = date.today()
                effective_on = schedule.effective_on
                expires_on = schedule.expires_on
                start_date = max(today, effective_on)
                end_date = expires_on
                # Get the dates that match the day_of_week
                dates = get_dates_between(start_date, end_date, schedule.day_of_week)
                for appointment_date in dates:
                    # For each date, generate appointment slots
                    # Convert times to datetime objects
                    start_datetime = datetime.combine(
                        appointment_date, schedule.start_time
                    )
                    end_datetime = datetime.combine(appointment_date, schedule.end_time)
                    current_time = start_datetime
                    while current_time < end_datetime:
                        for duration in durations:
                            duration_td = timedelta(minutes=duration)
                            if current_time + duration_td <= end_datetime:
                                # Decide randomly whether to create an appointment
                                if random.choice([True, False]):  # 50% chance
                                    # Generate an appointment
                                    appointment = Appointment(
                                        associate_id=associate.id,
                                        date=appointment_date,
                                        start_time=current_time.time(),
                                        end_time=(current_time + duration_td).time(),
                                    )

                                    # Check if appointment already exists
                                    existing_appointment = session.exec(
                                        select(Appointment).where(
                                            Appointment.associate_id == associate.id,
                                            Appointment.date == appointment_date,
                                            Appointment.start_time
                                            == current_time.time(),
                                            Appointment.end_time
                                            == (current_time + duration_td).time(),
                                        )
                                    ).first()
                                    if existing_appointment:
                                        print(
                                            f"Appointment already exists for Associate ID: {associate.id} on {appointment_date} at {current_time.time()}"
                                        )
                                    else:
                                        # Create event in Google Calendar
                                        event = {
                                            "summary": "Appointment",
                                            "description": f"Appointment for Associate ID: {associate.id}",
                                            "start": {
                                                "dateTime": start_datetime.isoformat(),
                                                "timeZone": "America/New_York",  # Dynamically change timezone if needed
                                            },
                                            "end": {
                                                "dateTime": end_datetime.isoformat(),
                                                "timeZone": "America/New_York",  # Dynamically change timezone if needed
                                            },
                                        }
                                        calendar_event = calendar.add_event(associate.calendar_id, event)
                                        appointment.calendar_id = calendar_event.get("id", "")  # Set calendar_id

                                        session.add(appointment)
                                        print(
                                            f"Added appointment for Associate ID: {associate.id} on {appointment_date} from {current_time.time()} to {(current_time + duration_td).time()}"
                                        )
                                else:
                                    print(
                                        f"Skipped appointment slot for Associate ID: {associate.id} on {appointment_date} at {current_time.time()}"
                                    )
                                # Update current_time
                                current_time += duration_td
                                break
                        else:
                            # No duration fits, break the loop
                            break
                # Commit the session after each associate's appointments
                session.commit()


if __name__ == "__main__":
    generate_appointments()
