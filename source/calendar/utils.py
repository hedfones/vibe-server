from datetime import datetime

import pytz

from .model import Event


def get_event_dates(event: Event) -> tuple[datetime, datetime]:
    event_start = event["start"]
    dt = datetime.fromisoformat(event_start["dateTime"])
    if not dt.tzinfo:
        tz = pytz.timezone(event_start["timeZone"])
        event_start_dtz = tz.localize(dt)
    else:
        event_start_dtz = dt

    event_end = event["end"]
    dt = datetime.fromisoformat(event_end["dateTime"])
    if not dt.tzinfo:
        tz = pytz.timezone(event_end["timeZone"])
        event_end_dtz = tz.localize(dt)
    else:
        event_end_dtz = dt

    return event_start_dtz, event_end_dtz
