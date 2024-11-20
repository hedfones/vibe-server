import os
import random
import sys
from datetime import date, datetime, time, timedelta

from sqlmodel import Session, select

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(parent_dir)

from source import (
    DatabaseService,
    PostgresCredentials,
    SecretsManager,
)
from source.database.model import (
    Appointment,
    Associate,
    AssociateProductLink,
    Business,
    Location,
    LocationProductLink,
    Product,
    Schedule,
)


def main():
    secrets = SecretsManager("./.env")

    db_creds = PostgresCredentials(
        user=secrets.get("POSTGRES_USER"),
        password=secrets.get("POSTGRES_PASSWORD"),
        database=secrets.get("POSTGRES_DB"),
    )
    db = DatabaseService(db_creds)

    # Configurable parameters
    NUM_BUSINESSES = 2
    NUM_ASSOCIATES_PER_BUSINESS = 3
    NUM_LOCATIONS_PER_BUSINESS = 2
    DAYS_OF_WEEK = 5  # Monday-Friday schedules (for simplicity)
    NUM_APPOINTMENTS_PER_SCHEDULE = 5
    NUM_PRODUCTS_PER_BUSINESS = 3

    # Connect to a SQLite database (in-memory for demonstration)
    engine = db.engine

    # Functions to generate data
    def create_random_schedules(associate_id: int, location_id: int):
        schedules = []
        start_of_week = date.today()
        # We'll create a schedule for each weekday
        for day_of_week in range(DAYS_OF_WEEK):
            # For demonstration, assume Monday=0 through Friday=4
            schedule = Schedule(
                associate_id=associate_id,
                location_id=location_id,
                start_time=time(hour=9),  # Work starts at 9 AM
                end_time=time(hour=17),  # Work ends at 5 PM
                effective_on=start_of_week,
                expires_on=start_of_week + timedelta(days=365),  # Effective for a year
                day_of_week=day_of_week,
            )
            schedules.append(schedule)
        return schedules

    def create_appointments_for_schedule(associate_id: int, schedule: Schedule):
        appointments = []
        current_date = schedule.effective_on
        # We'll create appointments for the first `NUM_APPOINTMENTS_PER_SCHEDULE` valid days
        created_appointments_count = 0
        delta_days = 0
        while created_appointments_count < NUM_APPOINTMENTS_PER_SCHEDULE:
            # Find the next date corresponding to the schedule's day_of_week
            next_date = current_date + timedelta(days=delta_days)
            if next_date.weekday() == schedule.day_of_week:
                # Ensure the appointment date is within the schedule's effective range
                if next_date > schedule.expires_on:
                    break
                # For demonstration, create 30-minute appointments
                appointment_start = datetime.combine(next_date, schedule.start_time)
                appointment_end = appointment_start + timedelta(minutes=30)
                appointment = Appointment(
                    associate_id=associate_id,
                    date=next_date,
                    start_time=schedule.start_time,
                    end_time=appointment_end.time(),
                )
                appointments.append(appointment)
                created_appointments_count += 1
            delta_days += 1
        return appointments

    def create_products_for_business(business_id: int):
        products = []
        for _ in range(NUM_PRODUCTS_PER_BUSINESS):
            product = Product(
                business_id=business_id,
                duration_minutes=random.choice([30, 45, 60]),  # product durations
            )
            products.append(product)
        return products

    # Main data generation
    with Session(engine) as session:
        for b in range(NUM_BUSINESSES):
            business = Business(
                assistant_id=f"assistant_{b}",
            )
            session.add(business)
            session.commit()  # commit to get business.id

            # Create associates for the business
            associates = []
            for _ in range(NUM_ASSOCIATES_PER_BUSINESS):
                associate = Associate(
                    business_id=business.id,
                )
                session.add(associate)
                associates.append(associate)

            # Create locations for the business
            locations = []
            for _ in range(NUM_LOCATIONS_PER_BUSINESS):
                location = Location(
                    business_id=business.id,
                )
                session.add(location)
                locations.append(location)

            session.commit()  # commit to get IDs for associates and locations

            # Create products for the business
            products = create_products_for_business(business.id)
            for product in products:
                session.add(product)
            session.commit()  # commit to get product IDs

            # Link products to locations and associates (LocationProductLink & AssociateProductLink)
            for product in products:
                for location in locations:
                    location_product_link = LocationProductLink(
                        location_id=location.id, product_id=product.id
                    )
                    session.add(location_product_link)
                for associate in associates:
                    associate_product_link = AssociateProductLink(
                        associate_id=associate.id, product_id=product.id
                    )
                    session.add(associate_product_link)
            session.commit()

            # Create schedules and appointments for each associate at each location
            for associate in associates:
                for location in locations:
                    schedules = create_random_schedules(associate.id, location.id)
                    for schedule in schedules:
                        session.add(schedule)
                    session.commit()  # commit schedules to get schedule.id

                    # Create appointments for each schedule
                    for schedule in schedules:
                        appointments = create_appointments_for_schedule(
                            associate.id, schedule
                        )
                        for appointment in appointments:
                            session.add(appointment)
                    session.commit()

        # Final commit
        session.commit()

    print("Data generation complete.")

    # Verification of counts (optional)
    with Session(engine) as session:
        business_count = len(session.exec(select(Business)).all())
        associates_count = len(session.exec(select(Associate)).all())
        locations_count = len(session.exec(select(Location)).all())
        products_count = len(session.exec(select(Product)).all())
        schedules_count = len(session.exec(select(Schedule)).all())
        appointments_count = len(session.exec(select(Appointment)).all())
        location_product_link_count = len(
            session.exec(select(LocationProductLink)).all()
        )
        associate_product_link_count = len(
            session.exec(select(AssociateProductLink)).all()
        )

    print(f"Businesses: {business_count}")
    print(f"Associates: {associates_count}")
    print(f"Locations: {locations_count}")
    print(f"Products: {products_count}")
    print(f"Schedules: {schedules_count}")
    print(f"Appointments: {appointments_count}")
    print(f"Location-Product Links: {location_product_link_count}")
    print(f"Associate-Product Links: {associate_product_link_count}")


if __name__ == "__main__":
    main()
