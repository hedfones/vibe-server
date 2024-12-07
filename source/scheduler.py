from datetime import datetime

from .database import (
    DatabaseService,
)
from .model import AvailabilityWindow


class Scheduler:
    def __init__(self, db: DatabaseService) -> None:
        self.db: DatabaseService = db

    def split_window(
        self, window: AvailabilityWindow, start_dt: datetime, end_dt: datetime
    ) -> tuple[AvailabilityWindow, AvailabilityWindow]:
        before_window = AvailabilityWindow(start_time=window.start_time, end_time=start_dt)
        after_window = AvailabilityWindow(start_time=end_dt, end_time=window.end_time)
        return before_window, after_window

    def get_associate_available_windows(
        self, associate_id: int, location_id: int, product_duration_minutes: int
    ) -> list[AvailabilityWindow]:
        windows: dict[int, list[AvailabilityWindow]] = {}

        appointments = self.db.get_schedules_appointments_by_location_associate(location_id, associate_id)
        for schedule, appointment in appointments:
            if schedule.id not in windows:
                start_dt = datetime.combine(appointment.date, schedule.start_time)
                end_dt = datetime.combine(appointment.date, schedule.end_time)
                windows[schedule.id] = [AvailabilityWindow(start_time=start_dt, end_time=end_dt)]

            start_dt = datetime.combine(appointment.date, appointment.start_time)
            end_dt = datetime.combine(appointment.date, appointment.end_time)

            for i, window in enumerate(windows[schedule.id]):
                if window.start_time <= start_dt and end_dt <= window.end_time:
                    new_windows = self.split_window(window, start_dt, end_dt)
                    new_windows = [w for w in new_windows if w.duration_minutes >= product_duration_minutes]

                    _ = windows[schedule.id].pop(i)
                    windows[schedule.id].extend(new_windows)

        window_list: list[AvailabilityWindow] = []
        for sublist in windows.values():
            window_list.extend(sublist)

        for window in window_list:
            window.associate_id = associate_id
        return window_list

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
