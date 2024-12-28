from datetime import datetime, timedelta

import pytz

from .calendar_service import GoogleCalendarOAuth2
from .database import DatabaseService
from .model import Appointment, AvailabilityWindow


class Scheduler:
    def __init__(self, db: DatabaseService, calendar: GoogleCalendarOAuth2) -> None:
        """Initializes the Scheduler with database and calendar services.

        Args:
            db: An instance of DatabaseService used for database operations.
            calendar: An instance of GoogleCalendar used for calendar operations.
        """
        self.db: DatabaseService = db
        self.calendar: GoogleCalendarOAuth2 = calendar

    def split_window(
        self, window: AvailabilityWindow, start_dt: datetime, end_dt: datetime
    ) -> list[AvailabilityWindow]:
        """Splits an availability window into two if the new booking overlaps.

        Args:
            window: The original availability window.
            start_dt: The start datetime of the new booking.
            end_dt: The end datetime of the new booking.

        Returns:
            A list of new AvailabilityWindow instances resulting from the split.
        """
        new_windows: list[AvailabilityWindow] = []
        if start_dt > window.start_time:
            new_windows.append(AvailabilityWindow(start_time=window.start_time, end_time=start_dt))
        if end_dt < window.end_time:
            new_windows.append(AvailabilityWindow(start_time=end_dt, end_time=window.end_time))
        return new_windows

    def get_appointments_by_associate_id(self, associate_id: int) -> list[Appointment]:
        """Retrieves appointments for a given associate within the next 180 days.

        Args:
            associate_id: The unique identifier for the associate.

        Returns:
            A sorted list of the associate's appointments.
        """
        associate = self.db.get_associate_by_id(associate_id)
        assert associate is not None, f"Associate with ID {associate_id} not found."

        # Define the timeframe for fetching appointments
        start = datetime.now(pytz.UTC)
        end = start + timedelta(days=180)

        # Read appointments from the calendar
        events = self.calendar.read_appointments(associate.calendar_id, start, end)
        appointments = [Appointment.from_event(event) for event in events]

        # Sort appointments by start time
        appointments = sorted(appointments, key=lambda x: x.start)
        return appointments

    def get_associate_available_windows(
        self, associate_id: int, location_id: int, product_duration_minutes: int
    ) -> list[AvailabilityWindow]:
        """Calculates availability windows for an associate considering their appointments.

        Args:
            associate_id: The unique identifier for the associate.
            location_id: The unique identifier for the location.
            product_duration_minutes: The duration of the product (appointment) in minutes.

        Returns:
            A list of available windows for the associate.
        """
        # Retrieve appointments and schedules
        appointments = self.get_appointments_by_associate_id(associate_id)
        schedules = self.db.get_going_forward_schedules_by_location_associate(location_id, associate_id)

        # Generate initial availability windows from schedules
        windows: list[AvailabilityWindow] = []
        for schedule in schedules:
            windows.append(AvailabilityWindow(start_time=schedule.start_dtz, end_time=schedule.end_dtz))

        # Adjust windows based on appointments
        for appointment in appointments:
            split_window_indices: list[int] = []
            extended_windows: list[AvailabilityWindow] = []
            for i, window in enumerate(windows):
                if appointment.start > window.end_time:
                    continue
                if appointment.end < window.start_time:
                    continue

                split_window_indices.append(i)

                # Split windows where appointments overlap
                new_windows = self.split_window(window, appointment.start, appointment.end)
                # Filter windows based on the required product duration
                new_windows = [w for w in new_windows if w.duration_minutes >= product_duration_minutes]
                extended_windows.extend(new_windows)

            # Remove windows that were split
            for i in split_window_indices:
                _ = windows.pop(i)

            # Add new windows to the list
            windows.extend(extended_windows)

        # Assign associate ID to each window
        for window in windows:
            window.associate_id = associate_id
        return windows

    def get_availabilities(
        self, product_id: int, product_duration_minutes: int, location_id: int
    ) -> list[AvailabilityWindow]:
        """Gets available windows for all associates for a specific product and location.

        Args:
            product_id: The unique identifier for the product.
            product_duration_minutes: The duration of the product (appointment) in minutes.
            location_id: The unique identifier for the location.

        Returns:
            A list of availability windows across all relevant associates.
        """
        # Retrieve associates based on product and location
        associates = self.db.get_associates_by_location_product(location_id, product_id)

        results: list[AvailabilityWindow] = []

        # TODO: Handle duplicate associates
        for associate in associates:
            # Get available windows for each associate
            availability = self.get_associate_available_windows(associate.id, location_id, product_duration_minutes)
            results.extend(availability)

        return results
