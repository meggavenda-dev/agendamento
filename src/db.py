from supabase import create_client
import streamlit as st

@st.cache_resource
def get_supabase():
    url = (st.secrets.get("SUPABASE_URL") or "").strip()
    key = (st.secrets.get("SUPABASE_KEY") or "").strip()
    if not url or not key:
        raise RuntimeError("Faltam SUPABASE_URL e/ou SUPABASE_KEY nos Secrets.")
    return create_client(url, key)

def fetch_settings():
    sb = get_supabase()
    res = sb.table("settings").select("value").eq("key", "scheduler").single().execute()
    return res.data["value"] if res.data else {}

def clinics_upsert(rows: list[dict]):
    sb = get_supabase()
    return sb.table("clinics").upsert(rows).execute()

def clinics_get_by_id(clinic_id: int):
    sb = get_supabase()
    try:
        res = sb.table("clinics").select("*").eq("clinic_id", clinic_id).limit(1).execute()
        return res.data[0] if res.data else None
    except Exception:
        return None

def clinics_update(clinic_id: int, payload: dict):
    sb = get_supabase()
    return sb.table("clinics").update(payload).eq("clinic_id", clinic_id).execute()

def apply_clinic_status_from_visit(clinic_id: int, visit_status: str):
    if visit_status == "Fechado Parceria":
        clinics_update(clinic_id, {"status": "Ativo"})
    elif visit_status == "Sem Parceria":
        clinics_update(clinic_id, {"status": "Perdido"})

def clinic_has_any_visit(clinic_id: int) -> bool:
    sb = get_supabase()
    res = sb.table("visits").select("visit_id").eq("clinic_id", clinic_id).limit(1).execute()
    return bool(res.data)

def visits_list_by_date(date_iso: str):
    sb = get_supabase()
    start = f"{date_iso}T00:00:00"
    end = f"{date_iso}T23:59:59"
    return sb.table("visits").select("*, clinics(legal_name,status)").gte("start_at", start).lte("start_at", end).order("start_at").execute()

def visits_list_range(start_iso: str, end_iso: str):
    sb = get_supabase()
    return sb.table("visits").select("*, clinics(legal_name,status)").gte("start_at", start_iso).lte("start_at", end_iso).order("start_at").execute()

def visits_create(payload: dict):
    sb = get_supabase()
    return sb.table("visits").insert(payload).execute()

def visits_update(visit_id: int, payload: dict):
    sb = get_supabase()
    return sb.table("visits").update(payload).eq("visit_id", visit_id).execute()

def visits_delete(visit_id: int):
    sb = get_supabase()
    return sb.table("visits").delete().eq("visit_id", visit_id).execute()

def tasks_list_overdue(today_iso: str):
    sb = get_supabase()
    return sb.table("tasks").select("*, clinics(legal_name)").lt("due_date", today_iso).neq("status", "Concluída").order("due_date").execute()

def tasks_list_by_filters(status=None, clinic_id=None):
    sb = get_supabase()
    q = sb.table("tasks").select("*, clinics(legal_name)").order("due_date")
    if status:
        q = q.eq("status", status)
    if clinic_id:
        q = q.eq("clinic_id", clinic_id)
    return q.execute()

def task_create(payload: dict):
    sb = get_supabase()
    return sb.table("tasks").insert(payload).execute()

def task_update(task_id: int, payload: dict):
    sb = get_supabase()
    return sb.table("tasks").update(payload).eq("task_id", task_id).execute()
