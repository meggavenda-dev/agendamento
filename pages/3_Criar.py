# pages/3_Criar.py
import streamlit as st
from datetime import datetime, timedelta, timezone, time as dtime
import pytz

# Fallback de import para ambientes que não reconhecem o pacote core
try:
    from core.auth import require_auth
    from core.supa import supabase_user
    from core.queries import get_profile
    from core.ui import load_css
except ImportError:
    import os, sys
    APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if APP_ROOT not in sys.path:
        sys.path.insert(0, APP_ROOT)
    from core.auth import require_auth
    from core.supa import supabase_user
    from core.queries import get_profile
    from core.ui import load_css

st.set_page_config(page_title="Criar • PulseAgenda", layout="wide")

uid = require_auth()
sb = supabase_user()
prof = get_profile(sb, uid) or {}

tz_name = prof.get("timezone", "America/Sao_Paulo")
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

try:
    tz = pytz.timezone(tz_name)
except Exception:
    tz = pytz.timezone("America/Sao_Paulo")

st.title("Criar")

# ==========================================
# Funções auxiliares
# ==========================================
def _now_local_rounded(hours_ahead: int = 2):
    base = datetime.now(tz) + timedelta(hours=hours_ahead)
    return base.replace(second=0, microsecond=0)

def _compose_dt_from_date_time(date_value, time_value, fallback_hours=2):
    if date_value is None:
        date_value = datetime.now(tz).date()
    if time_value is None:
        h = min(max(0, _now_local_rounded(fallback_hours).hour), 23)
        m = _now_local_rounded(fallback_hours).minute
        time_value = dtime(h, m)
    local_naive = datetime.combine(date_value, time_value)
    try:
        local_dt = tz.localize(local_naive)
    except Exception:
        if local_naive.tzinfo is None:
            local_dt = local_naive.replace(tzinfo=timezone.utc).astimezone(tz)
        else:
            local_dt = local_naive
    return local_dt

_has_datetime_input = hasattr(st, "datetime_input")

# ==========================================
# Formulário
# ==========================================
with st.form("create", clear_on_submit=False):
    itype = st.selectbox("Tipo", ["task", "meeting", "event"], index=0)
    title = st.text_input("Título*")
    tag = st.text_input("Tag", value="geral")
    priority = st.select_slider("Prioridade", options=[1,2,3,4], value=2)
    estimated = st.number_input("Estimado (min)", min_value=5, max_value=480, value=30, step=5)

    # Data/hora com fallback
    if _has_datetime_input:
        default_dt = _now_local_rounded(2)
        due_local_dt = st.datetime_input("Prazo/Horário", value=default_dt, key="due_dt")
        if due_local_dt.tzinfo is None:
            due_local = tz.localize(due_local_dt)
        else:
            due_local = due_local_dt.astimezone(tz)
    else:
        st.caption("Seu ambiente não suporta `st.datetime_input`. Usando data e hora separadas.")
        default_dt = _now_local_rounded(2)
        due_date = st.date_input("Data", value=default_dt.date(), key="due_date")
        due_time = st.time_input("Hora", value=default_dt.time(), step=300, key="due_time")
        due_local = _compose_dt_from_date_time(due_date, due_time, fallback_hours=2)

    # Recorrência com rótulos PT-BR (valor salvo em inglês)
    recurrence_labels = {
        "Sem repetição": "none",
        "Diariamente": "daily",
        "Semanalmente": "weekly",
        "Mensalmente": "monthly",
        "Dias úteis (Seg a Sex)": "workdays",
        "A cada X dias": "every_x_days",
    }
    recurrence_pt = st.selectbox("Regra", list(recurrence_labels.keys()), index=0)
    recurrence = recurrence_labels[recurrence_pt]

    recur_interval = int(st.number_input("Intervalo (para 'A cada X dias')", min_value=1, max_value=30, value=1))
    recur_weekdays = st.text_input("Dias semana (mon,tue,wed,...)", value="")

    submitted = st.form_submit_button("Salvar", use_container_width=True)

# ==========================================
# Salvar item
# ==========================================
if submitted:
    if not title.strip():
        st.error("Título obrigatório."); st.stop()

    try:
        if due_local.tzinfo is None:
            due_local = tz.localize(due_local)
    except Exception:
        due_local = due_local.replace(tzinfo=timezone.utc).astimezone(tz)

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
        st.success("Criado com sucesso!")
    except Exception as e:
        st.error(f"Erro: {e}")
