from __future__ import annotations

from .supabase import get_supabase, data_or_raise


def upsert(rows: list[dict]):
    sb = get_supabase()
    res = sb.table("clinics").upsert(rows).execute()
    return data_or_raise(res, "clinics.upsert")


def get_by_id(clinic_id: int) -> dict | None:
    sb = get_supabase()
    res = sb.table("clinics").select("*").eq("clinic_id", clinic_id).limit(1).execute()
    d = data_or_raise(res, "clinics.get_by_id") or []
    return d[0] if d else None


def update(clinic_id: int, payload: dict):
    sb = get_supabase()
    res = sb.table("clinics").update(payload).eq("clinic_id", clinic_id).execute()
    return data_or_raise(res, "clinics.update")
