# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Optional
from supabase import create_client
import streamlit as st


@st.cache_resource
def get_supabase():
    url = (st.secrets.get("SUPABASE_URL") or "").strip()
    key = (st.secrets.get("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("Faltam SUPABASE_URL e/ou SUPABASE_KEY nos Secrets.")
    return create_client(url, key)


# ---------------- Settings ----------------

def fetch_settings() -> dict:
    sb = get_supabase()
    res = sb.table("settings").select("value").eq("key", "scheduler").single().execute()
    return res.data["value"] if res.data else {}


# ---------------- Clinics ----------------

def clinics_upsert(rows: list[dict]):
    sb = get_supabase()
    return sb.table("clinics").upsert(rows).execute()


def clinics_get_by_id(clinic_id: int):
    sb = get_supabase()
    res = sb.table("clinics").select("*").eq("clinic_id", int(clinic_id)).limit(1).execute()
    return res.data[0] if res.data else None


def clinics_update(clinic_id: int, payload: dict):
    sb = get_supabase()
    return sb.table("clinics").update(payload).eq("clinic_id", int(clinic_id)).execute()


def clinics_list(filters: Optional[dict] = None, limit: int = 5000):
    sb = get_supabase()
    q = sb.table("clinics").select("*").order("updated_at", desc=True).limit(limit)
    filters = filters or {}
    for k, v in filters.items():
        if v is None or v == "":
            continue
        q = q.eq(k, v)
    return q.execute()


# ---------------- Visits ----------------

def visits_list_by_date(date_iso: str):
    sb = get_supabase()
    start = f"{date_iso}T00:00:00"
    end = f"{date_iso}T23:59:59"
    return (
        sb.table("visits")
        .select("*, clinics(legal_name,lead_status,interest_level,probability,potential_value)")
        .gte("start_at", start)
        .lte("start_at", end)
        .order("start_at")
        .execute()
    )


def visits_list_range(start_iso: str, end_iso: str):
    sb = get_supabase()
    return (
        sb.table("visits")
        .select("*, clinics(legal_name,lead_status,interest_level,probability,potential_value)")
        .gte("start_at", start_iso)
        .lte("start_at", end_iso)
        .order("start_at")
        .execute()
    )


def visits_list_by_clinic(clinic_id: int, limit: int = 500):
    sb = get_supabase()
    return (
        sb.table("visits")
        .select("*")
        .eq("clinic_id", int(clinic_id))
        .order("start_at", desc=True)
        .limit(limit)
        .execute()
    )


def visits_create(payload: dict):
    sb = get_supabase()
    return sb.table("visits").insert(payload).execute()


def visits_update(visit_id: int, payload: dict):
    sb = get_supabase()
    return sb.table("visits").update(payload).eq("visit_id", int(visit_id)).execute()


def visits_delete(visit_id: int):
    sb = get_supabase()
    return sb.table("visits").delete().eq("visit_id", int(visit_id)).execute()


def visit_history_add(visit_id: int, action: str, old: dict | None, new: dict | None):
    sb = get_supabase()
    return sb.table("visit_history").insert({
        "visit_id": int(visit_id),
        "action": action,
        "old": old,
        "new": new,
    }).execute()


def apply_clinic_status_from_visit(clinic_id: int, visit_status: str):
    # Mapeia eventos de visita para etapa do funil (lead_status)
    if visit_status == "Fechado Parceria":
        clinics_update(clinic_id, {"lead_status": "Fechado"})
    elif visit_status == "Sem Parceria":
        clinics_update(clinic_id, {"lead_status": "Perdido"})


# ---------------- Participants ----------------

def participants_list(visit_id: int):
    sb = get_supabase()
    return sb.table("visit_participants").select("*").eq("visit_id", int(visit_id)).order("participant_id").execute()


def participant_add(payload: dict):
    sb = get_supabase()
    return sb.table("visit_participants").insert(payload).execute()


def participant_delete(participant_id: int):
    sb = get_supabase()
    return sb.table("visit_participants").delete().eq("participant_id", int(participant_id)).execute()


# ---------------- Tasks ----------------

def tasks_list_overdue(today_iso: str):
    sb = get_supabase()
    return (
        sb.table("tasks")
        .select("*, clinics(legal_name,lead_status)")
        .lt("due_date", today_iso)
        .neq("status", "Concluída")
        .order("due_date")
        .execute()
    )


def tasks_list_by_filters(status=None, clinic_id=None, only_critical: bool = False, limit: int = 2000):
    sb = get_supabase()
    q = sb.table("tasks").select("*, clinics(legal_name,lead_status)").order("due_date", desc=False).limit(limit)
    if status:
        q = q.eq("status", status)
    if clinic_id:
        q = q.eq("clinic_id", int(clinic_id))
    if only_critical:
        q = q.or_("priority.eq.1,impact.eq.Alto")
    return q.execute()


def tasks_list_without_due(limit: int = 2000):
    sb = get_supabase()
    return (
        sb.table("tasks")
        .select("*, clinics(legal_name)")
        .is_("due_date", "null")
        .neq("status", "Concluída")
        .limit(limit)
        .execute()
    )


def task_create(payload: dict):
    sb = get_supabase()
    return sb.table("tasks").insert(payload).execute()


def task_update(task_id: int, payload: dict):
    sb = get_supabase()
    return sb.table("tasks").update(payload).eq("task_id", int(task_id)).execute()


# ---------------- Alerts / Queries ----------------

def clinics_without_next_action(limit: int = 200):
    sb = get_supabase()
    # Sem next_action_due e não perdido/fechado
    q = (
        sb.table("clinics")
        .select("clinic_id,legal_name,lead_status,interest_level,probability,potential_value")
        .is_("next_action_due", "null")
        .order("updated_at", desc=True)
        .limit(limit)
    )
    q = q.not_("lead_status", "in", "(Fechado,Perdido)")
    return q.execute()


def visits_realized_without_minutes(limit: int = 200):
    sb = get_supabase()
    return (
        sb.table("visits")
        .select("visit_id,clinic_id,start_at,status,ata_finalized,summary,discussion_rich, clinics(legal_name)")
        .eq("status", "Realizado")
        .or_("ata_finalized.is.false,discussion_rich.is.null")
        .order("start_at", desc=True)
        .limit(limit)
        .execute()
    )


def clinics_hot(limit: int = 200):
    sb = get_supabase()
    q = (
        sb.table("clinics")
        .select("clinic_id,legal_name,lead_status,interest_level,probability,potential_value,next_action,next_action_due")
        .or_("interest_level.eq.Alto,probability.gte.0.70")
        .order("probability", desc=True)
        .limit(limit)
    )
    q = q.not_("lead_status", "in", "(Fechado,Perdido)")
    return q.execute()
