import streamlit as st
from datetime import datetime, timedelta, timezone
import pytz
from core.auth import require_auth
from core.supa import supabase_user
from core.queries import get_profile
from core.ui import load_css

st.set_page_config(page_title="Criar • PulseAgenda", layout="wide")

uid = require_auth()
sb = supabase_user()
prof = get_profile(sb, uid) or {}
tz_name = prof.get("timezone","America/Sao_Paulo")
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

try:
    tz = pytz.timezone(tz_name)
except Exception:
    tz = pytz.timezone("America/Sao_Paulo")

st.title("Criar")
with st.form("create"):
    itype = st.selectbox("Tipo", ["task","meeting","event"], index=0)
    title = st.text_input("Título*")
    tag = st.text_input("Tag", value="geral")
    priority = st.select_slider("Prioridade", options=[1,2,3,4], value=2)
    due_local = st.datetime_input("Prazo/Horário", value=datetime.now(tz)+timedelta(hours=2))
    estimated = st.number_input("Estimado (min)", min_value=5, max_value=480, value=30, step=5)
    recurrence = st.selectbox("Recorrência", ["none","daily","weekly","monthly","workdays","every_x_days"], index=0)
    recur_interval = int(st.number_input("Intervalo", min_value=1, max_value=30, value=1))
    recur_weekdays = st.text_input("Dias semana (mon,tue,wed...)", value="")
    submitted = st.form_submit_button("Salvar", use_container_width=True)

if submitted:
    if not title.strip():
        st.error("Título obrigatório.")
        st.stop()
    if due_local.tzinfo is None:
        due_local = tz.localize(due_local)
    due_utc = due_local.astimezone(timezone.utc)
    item = {
        "user_id": uid,
        "type": itype,
        "title": title.strip(),
        "tag": tag.strip() or "geral",
        "priority": int(priority),
        "status": "todo",
        "due_at": due_utc.isoformat(),
        "estimated_minutes": int(estimated),
        "recurrence": recurrence,
        "recur_interval": int(recur_interval),
        "recur_weekdays": (recur_weekdays.strip() or None),
    }
    try:
        sb.table("items").insert(item).execute()
        st.success("Criado com sucesso")
    except Exception as e:
        st.error(f"Erro: {e}")
