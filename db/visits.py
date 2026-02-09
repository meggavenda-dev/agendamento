from __future__ import annotations

from datetime import date
from .supabase import get_supabase, data_or_raise
from core.time import local_day_bounds_utc


def list_by_local_date(d: date, tz_name: str) -> list[dict]:
    """Lista visitas por dia local, consultando o banco em UTC."""
    sb = get_supabase()
    start_utc, end_utc = local_day_bounds_utc(d, tz_name)
    res = (
        sb.table("visits")
        .select("*, clinics(legal_name,status)")
        .gte("start_at", start_utc)
        .lte("start_at", end_utc)
        .order("start_at")
        .execute()
    )
    return data_or_raise(res, "visits.list_by_local_date") or []


def list_range(start_utc_iso: str, end_utc_iso: str) -> list[dict]:
    sb = get_supabase()
    res = (
        sb.table("visits")
        .select("*, clinics(legal_name,status)")
        .gte("start_at", start_utc_iso)
        .lte("start_at", end_utc_iso)
        .order("start_at")
        .execute()
    )
    return data_or_raise(res, "visits.list_range") or []


def create(payload: dict):
    sb = get_supabase()
    res = sb.table("visits").insert(payload).execute()
    return data_or_raise(res, "visits.create")


def update(visit_id: int, payload: dict):
    sb = get_supabase()
    res = sb.table("visits").update(payload).eq("visit_id", visit_id).execute()
    return data_or_raise(res, "visits.update")


def delete(visit_id: int):
    sb = get_supabase()
    res = sb.table("visits").delete().eq("visit_id", visit_id).execute()
    return data_or_raise(res, "visits.delete")


def clinic_has_any_visit(clinic_id: int) -> bool:
    sb = get_supabase()
    res = sb.table("visits").select("visit_id").eq("clinic_id", clinic_id).limit(1).execute()
    d = data_or_raise(res, "visits.clinic_has_any_visit") or []
    return bool(d)
