import streamlit as st
from datetime import datetime, timedelta
import pytz

from core.auth import require_auth
from core.supa import supabase_user
from core.queries import fetch_semana, get_profile, week_range_for_tz
from core.ui import load_css, week_day_card, week_item_row

st.set_page_config(page_title="Semana • PulseAgenda", layout="wide")
load_css()

uid = require_auth()
sb = supabase_user()

profile = get_profile(sb, uid)
tz_name = profile.get("timezone", "America/Sao_Paulo")

st.title("🗓️ Semana")
st.caption("Visão completa com destaque no que importa agora")

items = fetch_semana(sb, uid, tz_name)

start_local, _, _, _, tz = week_range_for_tz(tz_name)
week_days = [start_local + timedelta(days=i) for i in range(7)]

bucket = {d.date().isoformat(): [] for d in week_days}

for it in items:
    due = it.get("due_at")
    if not due:
        continue
    dt_utc = datetime.fromisoformat(due.replace("Z", "+00:00"))
    dt_local = dt_utc.astimezone(tz)
    key = dt_local.date().isoformat()
    if key in bucket:
        bucket[key].append((dt_local, it))

for k in bucket:
    bucket[k].sort(key=lambda x: (x[1].get("priority", 3), x[0]))

now_local = datetime.now(tz)
today_key = now_local.date().isoformat()

labels = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]

html_cards = []
for i, d in enumerate(week_days):
    key = d.date().isoformat()
    is_today = (key == today_key)
    day_label = labels[i]

    if not bucket[key]:
        inner = "<div class='empty-day'>Aproveite para descansar<br/>ou planejar algo leve ✨</div>"
    else:
        rows = []
        for dt_local, it in bucket[key]:
            meta = f"⏰ {dt_local.strftime('%H:%M')} • {it.get('tag','geral')} • {it.get('type','task')}"
            rows.append(week_item_row(it.get("title", ""), meta, it.get("priority", 3)))
        inner = "".join(rows)

    html_cards.append(week_day_card(day_label, is_today, inner))

st.markdown("<div class='week-scroll'>" + "".join(html_cards) + "</div>", unsafe_allow_html=True)
st.divider()
st.caption("Dica Zen: deslize dia a dia. O card de hoje tem borda azul suave.")
