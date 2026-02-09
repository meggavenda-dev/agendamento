from __future__ import annotations

from .supabase import get_supabase, data_or_raise


def list_overdue(today_iso: str) -> list[dict]:
    sb = get_supabase()
    res = (
        sb.table("tasks")
        .select("*, clinics(legal_name)")
        .lt("due_date", today_iso)
        .neq("status", "Concluída")
        .order("due_date")
        .execute()
    )
    return data_or_raise(res, "tasks.list_overdue") or []


def list_by_filters(status: str | None = None, clinic_id: int | None = None) -> list[dict]:
    sb = get_supabase()
    q = sb.table("tasks").select("*, clinics(legal_name)").order("due_date")
    if status:
        q = q.eq("status", status)
    if clinic_id:
        q = q.eq("clinic_id", clinic_id)
    res = q.execute()
    return data_or_raise(res, "tasks.list_by_filters") or []


def create(payload: dict):
    sb = get_supabase()
    res = sb.table("tasks").insert(payload).execute()
    return data_or_raise(res, "tasks.create")


def update(task_id: int, payload: dict):
    sb = get_supabase()
    res = sb.table("tasks").update(payload).eq("task_id", task_id).execute()
    return data_or_raise(res, "tasks.update")
