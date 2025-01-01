import os
import sys

# Calculate the absolute path
source_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../."))
print(source_path)
sys.path.insert(0, source_path)

import random
from datetime import datetime, timedelta

import pytz
from dotenv import load_dotenv
from sqlmodel import Session

from source import db, get_calendar_by_business_id
from source.database import Schedule
# Assuming you've imported or defined:
# DatabaseService, PostgresCredentials, Business, Associate, Schedule, Product
# GoogleCalendar, and using the Event definition you provided
from source.google_service import Event  # Using the provided Event TypedDict

_ = load_dotenv(override=True)
calendar = get_calendar_by_business_id(1)


def generate_weekday_dates(start_date: datetime, end_date: datetime):
    """Generate all weekday (Mon-Fri) dates between start_date (inclusive) and end_date (exclusive)."""
    current = start_date
    while current < end_date:
        if current.weekday() < 5:  # Monday=0, Sunday=6
            yield current
        current += timedelta(days=1)


def create_schedules_and_appointments():
    tz = pytz.UTC
    now = datetime.now(tz)
    end_date = now + timedelta(days=90)  # next 3 months ~90 days

    schedule_start_hour = 12
    schedule_end_hour = 17

    associates = db.get_all_associates()
    if not associates:
        print("No associates found. Exiting.")
        return

    for associate in associates:
        # We'll assume associate has a calendar_id
        calendar_id = associate.calendar_id
        if not calendar_id:
            print(f"Associate {associate.id} has no calendar_id. Skipping appointments creation.")
            continue

        # Get locations for this associate
        locations = db.get_locations_by_associate_id(associate.id)
        if not locations:
            print(f"No locations found for associate {associate.id}. Skipping.")
            continue

        for d in generate_weekday_dates(now, end_date):
            start_dt = datetime(d.year, d.month, d.day, schedule_start_hour, 0, 0, tzinfo=tz)
            end_dt = datetime(d.year, d.month, d.day, schedule_end_hour, 0, 0, tzinfo=tz)

            # Select a location randomly (or you can pick based on other criteria)
            location = random.choice(locations)

            new_schedule = Schedule(
                associate_id=associate.id,
                location_id=location.id,
                start_datetime=start_dt,
                end_datetime=end_dt,
            )

            # Insert schedule into the DB
            with Session(db.engine) as session:
                session.add(new_schedule)
                session.commit()
                session.refresh(new_schedule)

            schedule_duration_hours = (end_dt - start_dt).seconds // 3600

            # Create random appointments within this schedule
            for hour_offset in range(schedule_duration_hours):
                # 5% chance to create an appointment
                if random.random() < 0.05:
                    appt_start = start_dt + timedelta(hours=hour_offset)
                    # Length 1 to 3 hours
                    duration = random.randint(1, 3)
                    appt_end = appt_start + timedelta(hours=duration)

                    # Check if the appointment fits entirely in the schedule
                    if appt_end > end_dt:
                        # Skip if it doesn't fit
                        continue

                    event: Event = {
                        "summary": f"Appointment with Associate {associate.id}",
                        "description": "Generated appointment",
                        "start": {"dateTime": appt_start.isoformat(), "timeZone": "UTC"},
                        "end": {"dateTime": appt_end.isoformat(), "timeZone": "UTC"},
                        "location": f"{location.description}",  # Location description or other info
                        "reminders": {"useDefault": True, "overrides": []},
                        # You can optionally add attendees or other fields:
                        # "attendees": [{"email": "client@example.com"}]
                    }

                    # Insert event into Google Calendar
                    created_event = calendar.add_event(calendar_id=calendar_id, event=event)
                    print(
                        f"Created event: {created_event['summary']} from {appt_start} to {appt_end} in calendar {calendar_id} at location {location.description}"
                    )


if __name__ == "__main__":
    create_schedules_and_appointments()
