
from datetime import datetime, timedelta, timezone
import pytz

def now_utc():
    return datetime.now(timezone.utc)

def get_profile(sb, user_id):
    try:
        d = sb.table("profiles").select("timezone,theme,email_notifications,whatsapp_notifications,whatsapp_number").eq("id", user_id).single().execute().data
        if isinstance(d, dict):
            d.setdefault("timezone","America/Sao_Paulo"); d.setdefault("theme","zen")
            return d
        return {"timezone":"America/Sao_Paulo","theme":"zen"}
    except Exception:
        return {"timezone":"America/Sao_Paulo","theme":"zen"}

def week_range_for_tz(tz_name: str):
    tz = pytz.timezone(tz_name or "America/Sao_Paulo")
    now_l = datetime.now(tz)
    start_l = (now_l - timedelta(days=now_l.weekday())).replace(hour=0,minute=0,second=0,microsecond=0)
    end_l = start_l + timedelta(days=7)
    return start_l, end_l, start_l.astimezone(pytz.utc), end_l.astimezone(pytz.utc), tz

def fetch_agora(sb, user_id, tz_name: str = "America/Sao_Paulo"):
    n = now_utc().replace(second=0,microsecond=0); next24=(n+timedelta(hours=24)).replace(second=0,microsecond=0)
    n_iso=n.isoformat(); next_iso=next24.isoformat()
    try:
        res = (sb.table("items").select("*").eq("user_id", user_id)
               .neq("status","done").or_(f"due_at.lt.{n_iso},and(due_at.gte.{n_iso},due_at.lte.{next_iso}),priority.lte.2")
               .order("priority",desc=False).order("due_at",desc=False).execute())
        return res.data or []
    except Exception:
        return []

def fetch_semana(sb, user_id, tz_name: str = "America/Sao_Paulo"):
    _,_,s,e,_ = week_range_for_tz(tz_name)
    s_iso=s.replace(microsecond=0).isoformat(); e_iso=e.replace(microsecond=0).isoformat()
    try:
        res=(sb.table("items").select("*").eq("user_id", user_id).neq("status","done")
             .not_.is_("due_at","null").gte("due_at", s_iso).lt("due_at", e_iso)
             .order("due_at",desc=False).order("priority",desc=False).execute())
        return res.data or []
    except Exception:
        return []
