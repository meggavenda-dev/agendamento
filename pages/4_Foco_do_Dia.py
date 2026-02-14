# pages/4_Foco_do_Dia.py
import os
import sys
import streamlit as st
from datetime import datetime, timedelta, timezone
import pytz

APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

from core.auth import require_auth
from core.supa import supabase_user
from core.queries import get_profile
from core.ui import load_css, priority_label

st.set_page_config(page_title="Foco do Dia • PulseAgenda", layout="wide")

sb = supabase_user()
uid = require_auth()

prof = get_profile(sb, uid) or {}
tz_name = prof.get("timezone", "America/Sao_Paulo")
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

try:
    tz = pytz.timezone(tz_name)
except Exception:
    tz = pytz.timezone("America/Sao_Paulo")

st.title("Foco do Dia")

start = datetime.now(tz).replace(hour=0, minute=0, second=0, microsecond=0)
end = start + timedelta(days=1)
s_iso = start.astimezone(timezone.utc).isoformat()
e_iso = end.astimezone(timezone.utc).isoformat()

items = (
    sb.table("items")
      .select("*")
      .eq("user_id", uid)
      .neq("status", "done")
      .gte("due_at", s_iso)
      .lt("due_at", e_iso)
      .order("priority", desc=False)
      .order("due_at", desc=False)
      .execute()
      .data or []
)

if not items:
    st.info("Sem itens para hoje. Planeje no 'Criar' ou 'Semana'.")
else:
    st.subheader("Top 3")
    for it in items[:3]:
        st.write(f"- {it['title']} ({priority_label(it.get('priority', 3))})")
