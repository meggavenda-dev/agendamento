
import os
from datetime import datetime, timezone, timedelta
from supabase import create_client
import pytz

def sb_service():
    return create_client(os.environ["SUPABASE_URL"], os.environ["SUPABASE_SERVICE_ROLE_KEY"])

def main():
    sb=sb_service(); now=datetime.now(timezone.utc)
    profiles=sb.table("profiles").select("id,timezone,auto_rollover_enabled,auto_bump_priority").execute().data or []
    for p in profiles:
        uid=p["id"]; tz=pytz.timezone(p.get("timezone") or "America/Sao_Paulo"); now_l=now.astimezone(tz)
        if p.get("auto_rollover_enabled",True) and 5<=now_l.hour<=7:
            items=sb.table("items").select("id,due_at").eq("user_id",uid).neq("status","done").lt("due_at", now.isoformat()).execute().data or []
            for it in items:
                try:
                    due=datetime.fromisoformat(it["due_at"].replace("Z","+00:00")).astimezone(tz)
                    new_due=now_l.replace(hour=due.hour,minute=due.minute,second=0,microsecond=0).astimezone(timezone.utc)
                    sb.table("items").update({"due_at": new_due.isoformat()}).eq("id",it["id"]).execute()
                except Exception: pass
        if p.get("auto_bump_priority",True):
            old=now - timedelta(hours=24)
            items=sb.table("items").select("id,priority,due_at").eq("user_id",uid).neq("status","done").lt("due_at", old.isoformat()).execute().data or []
            for it in items:
                try:
                    pr=int(it.get("priority") or 3)
                    if pr>1:
                        sb.table("items").update({"priority": pr-1}).eq("id",it["id"]).execute()
                except Exception: pass

if __name__=="__main__":
    main()
