# test_scheduler.py
from datetime import datetime, time
from unittest.mock import Mock

import pytest

from source import AvailabilityWindow, Scheduler
from source.database import Appointment, Associate, DatabaseService, Schedule


@pytest.fixture
def db_mock():
    # Create a mock for the DatabaseService class
    return Mock(spec=DatabaseService)


@pytest.fixture
def scheduler(db_mock):
    # Create an instance of Scheduler with the mocked DatabaseService
    return Scheduler(db=db_mock)


def test_split_window(scheduler):
    window = AvailabilityWindow(
        datetime(2023, 10, 15, 9, 0), datetime(2023, 10, 15, 17, 0)
    )
    start_dt = datetime(2023, 10, 15, 10, 0)
    end_dt = datetime(2023, 10, 15, 11, 0)

    before_window, after_window = scheduler.split_window(window, start_dt, end_dt)

    assert before_window.start_time == window.start_time
    assert before_window.end_time == start_dt
    assert after_window.start_time == end_dt
    assert after_window.end_time == window.end_time


def test_get_associate_available_windows_no_appointments(scheduler, db_mock):
    # Mocks
    associate_id = 1
    location_id = 2
    product_duration_minutes = 30

    # Set up the mock's return value
    db_mock.get_schedules_appointments_by_location_associate.return_value = []

    # Call the function
    available_windows = scheduler.get_associate_available_windows(
        associate_id, location_id, product_duration_minutes
    )

    # Verify
    assert available_windows == []


def test_get_associate_available_windows_with_appointments(scheduler, db_mock):
    # Mocks
    associate_id = 1
    location_id = 2
    product_duration_minutes = 30

    appointments_data = [
        (
            Schedule(
                id=1,
                associate_id=associate_id,
                location_id=location_id,
                start_time=time(9, 0),
                end_time=time(12, 0),
                effective_on=datetime.now().date(),
                expires_on=datetime.now().date(),
                day_of_week=0,
            ),
            Appointment(
                id=1,
                associate_id=associate_id,
                date=datetime(2023, 10, 15).date(),
                start_time=time(10, 0),
                end_time=time(10, 30),
            ),
        ),
    ]

    # Set up the mock's return value
    db_mock.get_schedules_appointments_by_location_associate.return_value = (
        appointments_data
    )

    # Call the function
    available_windows = scheduler.get_associate_available_windows(
        associate_id, location_id, product_duration_minutes
    )

    # Verify
    assert len(available_windows) == 2
    assert available_windows[0].start_time == datetime(2023, 10, 15, 9, 0)
    assert available_windows[0].end_time == datetime(2023, 10, 15, 10, 0)
    assert available_windows[1].start_time == datetime(2023, 10, 15, 10, 30)
    assert available_windows[1].end_time == datetime(2023, 10, 15, 12, 0)


def test_get_availabilities(scheduler, db_mock):
    # Mocks
    product_id = 1
    product_duration_minutes = 30
    location_id = 2

    associate = Associate(id=1, business_id=1)
    db_mock.get_associates_by_location_product.return_value = [associate]

    # Set up the mock's return value for the get_associate_available_windows method
    db_mock.get_schedules_appointments_by_location_associate.return_value = []

    # Call the function
    availabilities = scheduler.get_availabilities(
        product_id, product_duration_minutes, location_id
    )

    # Verify
    assert len(availabilities) == 1
    assert availabilities[0][0] == associate
    assert len(availabilities[0][1]) == 0


# if running the tests directly, enable the following lines
# if __name__ == "__main__":
#     pytest.main()
