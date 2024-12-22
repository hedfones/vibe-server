from datetime import datetime, timedelta

import pytz

from .calendar_service import GoogleCalendar
from .database import DatabaseService
from .model import Appointment, AvailabilityWindow


class Scheduler:
    def __init__(self, db: DatabaseService, calendar: GoogleCalendar) -> None:
        self.db: DatabaseService = db
        self.calendar: GoogleCalendar = calendar

    def split_window(
        self, window: AvailabilityWindow, start_dt: datetime, end_dt: datetime
    ) -> list[AvailabilityWindow]:
        new_windows: list[AvailabilityWindow] = []
        if start_dt > window.start_time:
            new_windows.append(AvailabilityWindow(start_time=window.start_time, end_time=start_dt))
        if end_dt < window.end_time:
            new_windows.append(AvailabilityWindow(start_time=end_dt, end_time=window.end_time))
        return new_windows

    def get_appointments_by_associate_id(self, associate_id: int) -> list[Appointment]:
        associate = self.db.get_associate_by_id(associate_id)
        assert associate is not None, f"Associate with ID {associate_id} not found."
        start = datetime.now(pytz.UTC)
        end = start + timedelta(days=180)
        events = self.calendar.read_appointments(associate.calendar_id, start, end)
        appointments = [Appointment.from_event(event) for event in events]
        appointments = sorted(appointments, key=lambda x: x.start)
        return appointments

    def get_associate_available_windows(
        self, associate_id: int, location_id: int, product_duration_minutes: int
    ) -> list[AvailabilityWindow]:
        appointments = self.get_appointments_by_associate_id(associate_id)
        schedules = self.db.get_going_forward_schedules_by_location_associate(location_id, associate_id)

        windows: list[AvailabilityWindow] = []
        for schedule in schedules:
            windows.append(AvailabilityWindow(start_time=schedule.start_dtz, end_time=schedule.end_dtz))

        for appointment in appointments:
            split_window_indices: list[int] = []
            extended_windows: list[AvailabilityWindow] = []
            for i, window in enumerate(windows):
                if appointment.start > window.end_time:
                    continue
                if appointment.end < window.start_time:
                    continue

                split_window_indices.append(i)

                new_windows = self.split_window(window, appointment.start, appointment.end)
                new_windows = [w for w in new_windows if w.duration_minutes >= product_duration_minutes]
                extended_windows.extend(new_windows)

            for i in split_window_indices:
                _ = windows.pop(i)

            windows.extend(extended_windows)

        for window in windows:
            window.associate_id = associate_id
        return windows

    def get_availabilities(
        self, product_id: int, product_duration_minutes: int, location_id: int
    ) -> list[AvailabilityWindow]:
        associates = self.db.get_associates_by_location_product(location_id, product_id)

        results: list[AvailabilityWindow] = []

        # TODO: Handle duplicate associates
        for associate in associates:
            availability = self.get_associate_available_windows(associate.id, location_id, product_duration_minutes)
            results.extend(availability)

        return results
