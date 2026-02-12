
import streamlit as st
from datetime import datetime, timedelta, timezone
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
st.caption("Navegue com setas, arraste para rolar ou use paginação")

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

# Lembrar última escolha
if "semana_mode" not in st.session_state:
    st.session_state["semana_mode"] = "Rolagem"

mode = st.segmented_control(
    "Navegação", options=["Rolagem", "Paginação"], default=st.session_state["semana_mode"], key="semana_mode"
)

# --- Paginação ---
if mode == "Paginação":
    per_page = st.select_slider("Cartões por página", options=[1,2,3], value=2, key="semana_per_page")
    if "semana_page" not in st.session_state:
        st.session_state["semana_page"] = 0
    total = len(html_cards)
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(st.session_state["semana_page"], pages - 1)

    p1,p2,p3,_ = st.columns([1,1,2,6])
    if p1.button("Anterior", use_container_width=True) and page > 0:
        st.session_state["semana_page"] = page - 1
        st.rerun()
    if p2.button("Próximo", use_container_width=True) and page < pages - 1:
        st.session_state["semana_page"] = page + 1
        st.rerun()
    p3.caption(f"Página {page+1}/{pages}")

    start = page * per_page
    end = min(start + per_page, total)
    subset = html_cards[start:end]
    st.markdown("<div class='pa-week'>" + "".join(subset) + "</div>", unsafe_allow_html=True)
    st.stop()

# --- Rolagem (setas, hoje, drag) ---
c1,c2,c3,c4 = st.columns([1,1,1,6])
left = c1.button("←", use_container_width=True)
today_btn = c2.button("Ir para Hoje", use_container_width=True)
right = c3.button("→", use_container_width=True)

st.markdown("<div id='pa-week-container' class='pa-week'>" + "".join(html_cards) + "</div>", unsafe_allow_html=True)

# Drag‑to‑scroll
st.markdown('''
<script>
(function() {
  const cont = document.getElementById('pa-week-container');
  if (!cont) return;
  let isDown = false; let startX, scrollLeft;
  const start = (e) => { isDown = true; startX = (e.touches ? e.touches[0].pageX : e.pageX) - cont.offsetLeft; scrollLeft = cont.scrollLeft; };
  const end   = () => { isDown = false; };
  const move  = (e) => { if (!isDown) return; e.preventDefault(); const x = (e.touches ? e.touches[0].pageX : e.pageX) - cont.offsetLeft; const walk = (x - startX); cont.scrollLeft = scrollLeft - walk; };
  cont.addEventListener('mousedown', start);
  cont.addEventListener('mouseleave', end);
  cont.addEventListener('mouseup', end);
  cont.addEventListener('mousemove', move);
  cont.addEventListener('touchstart', start, {passive: true});
  cont.addEventListener('touchend', end, {passive: true});
  cont.addEventListener('touchmove', move, {passive: false});
})();
</script>
''', unsafe_allow_html=True)

if left:
    st.markdown('''
    <script>
      const cont = document.getElementById('pa-week-container');
      if (cont) { cont.scrollBy({left: -360, behavior:'smooth'}); }
    </script>
    ''', unsafe_allow_html=True)

if right:
    st.markdown('''
    <script>
      const cont = document.getElementById('pa-week-container');
      if (cont) { cont.scrollBy({left: 360, behavior:'smooth'}); }
    </script>
    ''', unsafe_allow_html=True)

if today_btn:
    st.markdown('''
    <script>
      const cont = document.getElementById('pa-week-container');
      if (cont) {
        const t = cont.querySelector('.pa-day--today');
        if (t) {
          const off = t.offsetLeft - (cont.clientWidth/2 - t.clientWidth/2);
          cont.scrollTo({left: off, behavior: 'smooth'});
        }
      }
    </script>
    ''', unsafe_allow_html=True)
