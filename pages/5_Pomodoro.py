import streamlit as st
from datetime import datetime, timedelta, timezone
from core.auth import require_auth
from core.supa import supabase_user
from core.ui import load_css

st.set_page_config(page_title="Pomodoro • PulseAgenda", layout="wide")

uid = require_auth()
sb = supabase_user()

# Tema
try:
    prof = sb.table("profiles").select("theme").eq("id", uid).single().execute().data or {}
    focus = (prof.get("theme") == "focus")
except Exception:
    focus = False
load_css(focus_mode=focus)

st.title("Pomodoro")
st.caption("Foco em um item por vez")

items = (sb.table("items").select("id,title,estimated_minutes,spent_minutes")
         .eq("user_id", uid).neq("status","done").order("priority").execute().data or [])

if not items:
    st.info("Sem itens pendentes.")
    st.stop()

item_map = {f"{it['title']} ({it['id'][:6]})": it["id"] for it in items}
choice = st.selectbox("Escolha o item", list(item_map.keys()))
work_min = st.number_input("Foco (min)", min_value=10, max_value=120, value=25, step=5)
break_min = st.number_input("Pausa (min)", min_value=0, max_value=60, value=5, step=5)

if st.button("Iniciar"):
    st.session_state["pomodoro"] = {
        "item_id": item_map[choice],
        "start": datetime.now(timezone.utc).isoformat(),
        "work_min": int(work_min),
        "break_min": int(break_min),
        "phase": "work",
    }
    st.experimental_rerun()

session = st.session_state.get("pomodoro")
if session:
    start = datetime.fromisoformat(session["start"]) if session.get("start") else None
    phase = session.get("phase","work")
    dur = session["work_min"] if phase == "work" else session.get("break_min", 0)
    end = start + timedelta(minutes=dur)
    now = datetime.now(timezone.utc)
    remaining = max(0, int((end - now).total_seconds()))
    mm = remaining // 60
    ss = remaining % 60
    st.subheader(f"Fase: {'Foco' if phase=='work' else 'Pausa'} — {mm:02d}:{ss:02d}")
    st.caption("Atualize a página periodicamente para ver a contagem.")

    if remaining == 0:
        if phase == "work":
            try:
                it = sb.table("items").select("spent_minutes").eq("id", session["item_id"]).single().execute().data
                spent = int(it.get("spent_minutes") or 0)
            except Exception:
                spent = 0
            new_spent = spent + int(session["work_min"])
            sb.table("items").update({"spent_minutes": new_spent}).eq("id", session["item_id"]).eq("user_id", uid).execute()
            session["phase"] = "break" if session.get("break_min",0) > 0 else "done"
            session["start"] = datetime.now(timezone.utc).isoformat()
            st.session_state["pomodoro"] = session
            st.success("Foco concluído. Tempo contabilizado.")
        else:
            session["phase"] = "done"
            st.session_state["pomodoro"] = session
            st.info("Pausa concluída.")

    if phase == "done":
        c1, c2 = st.columns([1,1])
        if c1.button("Concluir item"):
            sb.table("items").update({"status":"done"}).eq("id", session["item_id"]).eq("user_id", uid).execute()
            st.session_state.pop("pomodoro", None)
            st.success("Item concluído")
        if c2.button("Nova sessão"):
            st.session_state.pop("pomodoro", None)
            st.experimental_rerun()
