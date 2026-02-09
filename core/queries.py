from datetime import datetime, timedelta, timezone
import pytz


def now_utc():
    return datetime.now(timezone.utc)


def get_profile(sb, user_id):
    try:
        return (
            sb.table("profiles")
            .select("timezone,theme,email_notifications,whatsapp_notifications,whatsapp_number,email,display_name")
            .eq("id", user_id)
            .single()
            .execute()
            .data
        )
    except Exception:
        return {"timezone": "America/Sao_Paulo", "theme": "zen"}


def week_range_for_tz(tz_name: str):
    tz = pytz.timezone(tz_name or "America/Sao_Paulo")
    now_local = datetime.now(tz)
    start_local = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
    end_local = start_local + timedelta(days=7)
    start_utc = start_local.astimezone(pytz.utc)
    end_utc = end_local.astimezone(pytz.utc)
    return start_local, end_local, start_utc, end_utc, tz


def fetch_agora(sb, user_id, tz_name: str = "America/Sao_Paulo"):
    n = now_utc()
    next24 = n + timedelta(hours=24)

    q1 = sb.table("items").select("*").eq("user_id", user_id).neq("status", "done").lt("due_at", n.isoformat()).execute()
    q2 = sb.table("items").select("*").eq("user_id", user_id).neq("status", "done").lte("due_at", next24.isoformat()).execute()
    q3 = sb.table("items").select("*").eq("user_id", user_id).neq("status", "done").in_("priority", [1, 2]).execute()

    items = {i["id"]: i for i in (q1.data or [])}
    for i in (q2.data or []):
        items[i["id"]] = i
    for i in (q3.data or []):
        items[i["id"]] = i

    def key(i):
        return (i.get("priority", 3), i.get("due_at") or "9999")

    return sorted(items.values(), key=key)


def fetch_semana(sb, user_id, tz_name: str = "America/Sao_Paulo"):
    _, _, start_utc, end_utc, _ = week_range_for_tz(tz_name)
    res = (
        sb.table("items")
        .select("*")
        .eq("user_id", user_id)
        .gte("due_at", start_utc.isoformat())
        .lt("due_at", end_utc.isoformat())
        .execute()
    )
    return res.data or []
