# pages/2_Semana.py
import streamlit as st
from datetime import datetime, timedelta, timezone

# Fallback de import para ambientes que não reconhecem o pacote core
try:
    from core.auth import require_auth
    from core.supa import supabase_user
    from core.queries import fetch_semana, get_profile, week_range_for_tz
    from core.ui import load_css, week_day_card, week_item_row
except ImportError:
    import os, sys
    APP_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if APP_ROOT not in sys.path:
        sys.path.insert(0, APP_ROOT)
    from core.auth import require_auth
    from core.supa import supabase_user
    from core.queries import fetch_semana, get_profile, week_range_for_tz
    from core.ui import load_css, week_day_card, week_item_row

st.set_page_config(page_title="Semana • PulseAgenda", layout="wide")

uid = require_auth()
sb = supabase_user()
prof = get_profile(sb, uid) or {}
tz_name = prof.get("timezone","America/Sao_Paulo")
focus = (prof.get("theme") == "focus")
load_css(focus_mode=focus)

st.title("Semana")

col_today, _ = st.columns([1,6])
go_today = col_today.button("Ir para Hoje", use_container_width=True)

items = fetch_semana(sb, uid, tz_name)
start_local, _, _, _, tz = week_range_for_tz(tz_name)
week_days = [start_local + timedelta(days=i) for i in range(7)]
labels = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"]

bucket = {d.date().isoformat(): [] for d in week_days}
for it in items:
    due = it.get("due_at")
    if not due:
        continue
    dt = datetime.fromisoformat(due.replace("Z","+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_local = dt.astimezone(tz)
    key = dt_local.date().isoformat()
    if key in bucket:
        bucket[key].append((dt_local, it))

for k in bucket:
    bucket[k].sort(key=lambda x: (x[1].get("priority",3), x[0]))

now_local = datetime.now(tz)
today_key = now_local.date().isoformat()

html_cards = []
for i, d in enumerate(week_days):
    key = d.date().isoformat()
    is_today = (key == today_key)
    if not bucket[key]:
        inner = "<div class='pa-day__empty'>Dia livre</div>"
    else:
        rows = []
        for dt_local, it in bucket[key]:
            meta = f"{dt_local.strftime('%H:%M')} • #{it.get('tag','geral')} • {it.get('type','task')}"
            rows.append(week_item_row(it.get('title',''), meta, it.get('priority',3)))
        inner = "".join(rows)
    html_cards.append(week_day_card(labels[i], is_today, inner))

st.markdown("<div id='pa-week' class='pa-week'>" + "".join(html_cards) + "</div>", unsafe_allow_html=True)

# Centralizar HOJE uma única vez por sessão (ou quando o botão é clicado)
if "semana_scrolled_today" not in st.session_state:
    st.session_state["semana_scrolled_today"] = False

if go_today or not st.session_state["semana_scrolled_today"]:
    st.markdown("""
    <script>
      const cont = document.getElementById('pa-week');
      if (cont) {
        const today = cont.querySelector('.pa-day--today');
        if (today) {
          const off = today.offsetLeft - (cont.clientWidth/2 - today.clientWidth/2);
          cont.scrollTo({ left: off, behavior: 'smooth' });
        }
      }
    </script>
    """, unsafe_allow_html=True)
    st.session_state["semana_scrolled_today"] = True
