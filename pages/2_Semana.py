
import streamlit as st
from datetime import datetime, timedelta
import pytz
from core.auth import require_auth
from core.supa import supabase_user
from core.queries import fetch_semana, get_profile, week_range_for_tz
from core.ui import load_css

st.set_page_config(page_title="Semana", layout="wide")
load_css(); uid = require_auth(); sb = supabase_user()
prof = get_profile(sb, uid); tz_name = prof.get("timezone","America/Sao_Paulo")
items = fetch_semana(sb, uid, tz_name)
start_local, _, _, _, tz = week_range_for_tz(tz_name)
week_days = [start_local + timedelta(days=i) for i in range(7)]

st.title("Semana")
for d in week_days:
    st.subheader(d.strftime("%A %d/%m").title())
    for it in items:
        due = it.get("due_at");
        if not due: continue
        dt = datetime.fromisoformat(due.replace("Z","+00:00")).astimezone(tz)
        if dt.date() == d.date():
            st.write("- ", dt.strftime("%H:%M"), it.get("title",""))
