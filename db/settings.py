from __future__ import annotations

from .supabase import get_supabase, data_or_raise


def fetch_settings() -> dict:
    sb = get_supabase()
    res = sb.table("settings").select("value").eq("key", "scheduler").single().execute()
    d = data_or_raise(res, "settings.fetch_scheduler")
    return (d or {}).get("value") or {}
