from __future__ import annotations

from datetime import datetime, timedelta, time, date
from dateutil import tz


def parse_hhmm(s: str) -> time:
    hh, mm = s.split(":")
    return time(int(hh), int(mm))


def build_slots(
    date_obj: date,
    tz_name: str,
    work_start: str = "08:00",
    work_end: str = "18:00",
    slot_minutes: int = 15,
    visit_minutes: int = 45,
):
    """Cria grade de slots (start,end) no timezone local."""
    zone = tz.gettz(tz_name)
    start_t = parse_hhmm(work_start)
    end_t = parse_hhmm(work_end)
    start_dt = datetime.combine(date_obj, start_t).replace(tzinfo=zone)
    end_limit = datetime.combine(date_obj, end_t).replace(tzinfo=zone)

    slots = []
    cursor = start_dt
    delta_slot = timedelta(minutes=slot_minutes)
    delta_visit = timedelta(minutes=visit_minutes)
    while cursor + delta_visit <= end_limit:
        slots.append((cursor, cursor + delta_visit))
        cursor += delta_slot
    return slots


def overlaps(a_start: datetime, a_end: datetime, b_start: datetime, b_end: datetime) -> bool:
    return a_start < b_end and b_start < a_end


def filter_available_slots(slots, existing_visits):
    available = []
    for s, e in slots:
        ok = True
        for v in existing_visits:
            if overlaps(s, e, v["start_at"], v["end_at"]):
                ok = False
                break
        if ok:
            available.append((s, e))
    return available


def assert_no_conflict(start_dt: datetime, end_dt: datetime, existing_visits):
    for v in existing_visits:
        if overlaps(start_dt, end_dt, v["start_at"], v["end_at"]):
            raise ValueError(
                f"Conflito com visita #{v.get('visit_id')} ({v['start_at']} - {v['end_at']})"
            )
