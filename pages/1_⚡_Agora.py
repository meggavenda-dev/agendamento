import streamlit as st
from core.auth import require_auth
from core.supa import supabase_anon
from core.queries import fetch_agora, get_profile
from core.ui import load_css, item_card

st.set_page_config(page_title="Agora • PulseAgenda", layout="wide")
load_css()

uid = require_auth()
sb = supabase_anon()
profile = get_profile(sb, uid)
tz_name = profile.get("timezone", "America/Sao_Paulo")

st.title("⚡ Agora")
st.caption("Atrasadas • Próximas 24h • Prioridades")

items = fetch_agora(sb, uid, tz_name)

if not items:
    st.info("Tudo em dia por aqui. Que tal planejar a semana? 🙂")
else:
    for it in items:
        item_card(it)
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Concluir", key=f"done_{it['id']}", use_container_width=True):
                sb.table("items").update({"status": "done"}).eq("id", it["id"]).execute()
                st.rerun()
        with c2:
            if st.button("⏳ Adiar 1 dia", key=f"delay_{it['id']}", use_container_width=True):
                import datetime
                due = it.get("due_at")
                if due:
                    dt = datetime.datetime.fromisoformat(due.replace("Z", "+00:00"))
                    dt = dt + datetime.timedelta(days=1)
                    sb.table("items").update({"due_at": dt.isoformat()}).eq("id", it["id"]).execute()
                    st.rerun()
