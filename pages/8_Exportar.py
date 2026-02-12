
import json
import streamlit as st
from datetime import datetime
from core.ui import load_css
from core.auth import require_auth
from core.supa import supabase_user

st.set_page_config(page_title="Exportar • PulseAgenda", layout="wide")

uid = require_auth()
sb = supabase_user()

try:
    prof = sb.table("profiles").select("theme").eq("id", uid).single().execute().data or {}
    focus = (prof.get("theme") == "focus")
except Exception:
    focus = False
load_css(focus_mode=focus)

st.title("Exportar")
st.caption("Baixe seus dados JSON")

def fetch_all(table, filt=None):
    q=sb.table(table).select("*")
    if filt:
        for k,v in filt.items(): q=q.eq(k,v)
    try: return q.execute().data or []
    except Exception: return []

items=fetch_all("items",{"user_id":uid}); reminders=fetch_all("reminders",{"user_id":uid}); tags=fetch_all("tags",{"user_id":uid}); profile=fetch_all("profiles",{"id":uid})
data={"exported_at":datetime.utcnow().isoformat()+"Z","items":items,"reminders":reminders,"tags":tags,"profile":(profile[0] if profile else {})}
st.download_button("Baixar JSON", data=json.dumps(data, ensure_ascii=False, indent=2), file_name="pulseagenda_export.json", mime="application/json")
